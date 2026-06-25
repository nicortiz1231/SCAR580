"""Clean sniper scope wiring and reduce recoil clip without moving ADS distance."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_sniper_scope_clean.log")
SNIPER_BP = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper"
CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
SCOPE_MESH = "/Game/BodycamFPSKIT/Demo/Meshes/SM_4xScopeForSniper.SM_4xScopeForSniper"
SET_MESH = "/Script/Engine.StaticMeshComponent:SetStaticMesh"
SET_VIS = "/Script/Engine.SceneComponent:SetVisibility"


def log(msg):
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[fix_sniper_clean] {msg}")


def connect_exec(a, b):
    return bool(a and b and a.try_create_connection(b))


def connect_data(a, b):
    return bool(a and b and a.try_create_connection(b))


def out_pin(node, name=None):
    if name:
        p = node.find_output_pin(name)
        if p:
            return p
    for p in unreal.BlueprintEditorLibrary.list_all_pins(node):
        if unreal.BlueprintGraphPinLibrary.get_pin_direction(p) == unreal.EdGraphPinDirection.EGPD_OUTPUT:
            return p
    return None


def rebuild_scope_chain(editor, exec_start_pin):
    """Insert SetStaticMesh(SM_4xScopeForSniper) -> SetVisibility(true) after exec_start_pin."""
    downstream = []
    if exec_start_pin:
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(exec_start_pin):
            if lp.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT:
                downstream.append(lp)

    set_mesh = editor.add_call_function_node(SET_MESH)
    set_vis = editor.add_call_function_node(SET_VIS)
    get_optic = editor.add_get_member_variable_node("OpticSight")
    connect_data(out_pin(get_optic), set_mesh.find_input_pin("self"))
    connect_data(out_pin(get_optic), set_vis.find_input_pin("self"))
    mesh_pin = set_mesh.find_input_pin("NewMesh")
    if mesh_pin:
        mesh_pin.set_pin_value(SCOPE_MESH)
    vis_pin = set_vis.find_input_pin("bNewVisibility")
    if vis_pin:
        vis_pin.set_pin_value("true")

    if exec_start_pin:
        exec_start_pin.break_pin_links()
        connect_exec(exec_start_pin, set_mesh.find_input_pin("execute"))
    connect_exec(set_mesh.find_output_pin("then"), set_vis.find_input_pin("execute"))
    for pin in downstream:
        connect_exec(set_vis.find_output_pin("then"), pin)
    return set_vis.find_output_pin("then")


def clean_graph_scope_nodes(editor, graph_label):
    remove = []
    for node in editor.list_all_nodes():
        cls = node.get_class().get_name()
        title = str(node.get_node_title())
        if cls == "K2Node_CallFunction" and ("SetStaticMesh" in title or "SetVisibility" in title):
            remove.append(node)
        if cls == "K2Node_VariableGet" and ("ScopeSightMesh" in title or "OpticSight" in title):
            # only remove if only used by removed nodes - skip for safety
            pass
    if remove:
        editor.remove_nodes(remove)
        log(f"Removed {len(remove)} old scope nodes from {graph_label}")


def wire_graph(editor, graph_label, parent_node, spawn_event_node=None):
    clean_graph_scope_nodes(editor, graph_label)
    if parent_node:
        rebuild_scope_chain(editor, parent_node.find_output_pin("then"))
        log(f"Rebuilt {graph_label} parent -> scope chain")
    if spawn_event_node:
        rebuild_scope_chain(editor, spawn_event_node.find_output_pin("then"))
        log(f"Rebuilt {graph_label} SpawnAttachments -> scope chain")


def fix_sniper(sniper_bp):
    scope_mesh = unreal.load_asset(SCOPE_MESH)
    cdo = unreal.get_default_object(sniper_bp.generated_class())
    cdo.set_editor_property("ScopeSightMesh", scope_mesh)
    cdo.set_editor_property("OpticSightMesh", scope_mesh)

    for gname in ("UserConstructionScript", "EventGraph"):
        graph = next((g for g in unreal.BlueprintEditorLibrary.list_graphs(sniper_bp) if g.get_name() == gname), None)
        if not graph:
            continue
        editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        parent = None
        spawn_ev = None
        for node in editor.list_all_nodes():
            if node.get_class().get_name() == "K2Node_CallParentFunction":
                t = str(node.get_node_title())
                if gname == "UserConstructionScript" and "Construction Script" in t:
                    parent = node
                if gname == "EventGraph" and "BeginPlay" in t:
                    parent = node
            if "SpawnAttachments" in str(node.get_node_title()):
                spawn_ev = node
        wire_graph(editor, gname, parent, spawn_ev if gname == "EventGraph" else None)

    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    seen = set()
    for handle in sds.k2_gather_subobject_data_for_blueprint(sniper_bp):
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(
            unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        )
        if not obj or "OpticSight" not in obj.get_name() or obj.get_class().get_name() != "StaticMeshComponent":
            continue
        if id(obj) in seen:
            continue
        seen.add(id(obj))
        obj.set_editor_property("static_mesh", scope_mesh)
        obj.set_editor_property("hidden_in_game", False)
    log("Updated sniper CDO + OpticSight template")


def tweak_recoil(sniper_bp):
    cdo = unreal.get_default_object(sniper_bp.generated_class())
    pv = cdo.get_editor_property("ProceduralValues")
    if not pv:
        return
    wv = pv.get_editor_property("WeaponValues")
    loc = wv.get_editor_property("BasePoseLoc")
    new_loc = unreal.Vector(float(loc.x) * 0.85, float(loc.y) * 0.65, float(loc.z) * 0.75)
    wv.set_editor_property("BasePoseLoc", new_loc)
    pv.set_editor_property("WeaponValues", wv)
    for prop in ("RecoilLoc", "RecoilRot", "RecoilTranslation", "RecoilRotation"):
        try:
            rv = pv.get_editor_property("RecoilValues")
            val = rv.get_editor_property(prop)
            if hasattr(val, "x"):
                rv.set_editor_property(
                    prop,
                    unreal.Vector(float(val.x) * 0.65, float(val.y) * 0.60, float(val.z) * 0.70),
                )
            pv.set_editor_property("RecoilValues", rv)
            log(f"Reduced RecoilValues.{prop}")
            break
        except Exception:
            pass
    pv.modify()
    unreal.EditorAssetLibrary.save_asset(pv.get_path_name(), only_if_is_dirty=False)
    log(f"BasePoseLoc -> ({new_loc.x:.2f},{new_loc.y:.2f},{new_loc.z:.2f})")


def main():
    if LOG.exists():
        LOG.unlink()
    sniper = unreal.load_asset(f"{SNIPER_BP}.BP_Weapon_Sniper")
    fix_sniper(sniper)
    tweak_recoil(sniper)
    sniper.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(sniper)
    unreal.EditorAssetLibrary.save_asset(SNIPER_BP, only_if_is_dirty=False)
    log("Done")

main()
