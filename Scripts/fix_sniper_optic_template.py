"""Set OpticSight blueprint template mesh + UCS; verify persisted."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_sniper_optic_template.log")
SNIPER_BP = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper"
SCOPE_MESH = "/Game/BodycamFPSKIT/Demo/Meshes/SM_4xScopeForSniper.SM_4xScopeForSniper"
SET_STATIC_MESH_FN = "/Script/Engine.StaticMeshComponent:SetStaticMesh"
SET_VISIBILITY_FN = "/Script/Engine.SceneComponent:SetVisibility"


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[optic_template] {msg}")


def connect_exec(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def connect_data(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def output_pin(node, preferred: str):
    pin = node.find_output_pin(preferred) if hasattr(node, "find_output_pin") else None
    if pin:
        return pin
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) == unreal.EdGraphPinDirection.EGPD_OUTPUT:
            return pin
    return None


def set_optic_template_mesh(sniper_bp, scope_mesh) -> None:
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    count = 0
    for handle in sds.k2_gather_subobject_data_for_blueprint(sniper_bp):
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
        if not obj or obj.get_class().get_name() != "StaticMeshComponent":
            continue
        if "OpticSight" not in obj.get_name():
            continue
        obj.set_editor_property("static_mesh", scope_mesh)
        obj.set_editor_property("hidden_in_game", False)
        obj.set_editor_property("visible", True)
        count += 1
        log(f"Template OpticSight mesh -> {scope_mesh.get_name()}")
    if not count:
        log("WARN: no OpticSight template found via subsystem")


def ensure_ucs_scope(sniper_bp) -> None:
    ucs = None
    for g in unreal.BlueprintEditorLibrary.list_graphs(sniper_bp):
        if g.get_name() == "UserConstructionScript":
            ucs = g
            break
    if not ucs:
        raise RuntimeError("Missing UCS")

    editor = unreal.BlueprintGraphEditor.get_graph_editor(ucs)
    for node in editor.list_all_nodes():
        if node.get_class().get_name() != "K2Node_CallFunction":
            continue
        if "SetStaticMesh" not in str(node.get_node_title()):
            continue
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            if str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin)) != "self":
                continue
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                if "OpticSight" in str(lp.get_owning_node().get_node_title()):
                    log("UCS already sets OpticSight mesh")
                    return

    parent = None
    for node in editor.list_all_nodes():
        if node.get_class().get_name() == "K2Node_CallParentFunction":
            parent = node
            break
    if not parent:
        raise RuntimeError("Missing parent UCS")

    set_mesh = editor.add_call_function_node(SET_STATIC_MESH_FN)
    set_vis = editor.add_call_function_node(SET_VISIBILITY_FN)
    get_optic = editor.add_get_member_variable_node("OpticSight")
    get_scope = editor.add_get_member_variable_node("ScopeSightMesh")
    if not all((set_mesh, set_vis, get_optic, get_scope)):
        raise RuntimeError("Failed creating UCS nodes")

    connect_data(output_pin(get_optic, "OpticSight"), set_mesh.find_input_pin("self"))
    connect_data(output_pin(get_scope, "ScopeSightMesh"), set_mesh.find_input_pin("NewMesh"))
    connect_data(output_pin(get_optic, "OpticSight"), set_vis.find_input_pin("self"))
    vis_pin = set_vis.find_input_pin("bNewVisibility")
    if vis_pin:
        vis_pin.set_pin_value("true")

    parent_then = parent.find_output_pin("then")
    parent_then.break_pin_links()
    connect_exec(parent_then, set_mesh.find_input_pin("execute"))
    connect_exec(set_mesh.find_output_pin("then"), set_vis.find_input_pin("execute"))
    log("UCS: Parent -> SetStaticMesh(ScopeSightMesh) -> SetVisibility")


def clean_eventgraph_to_stock_plus_scope(sniper_bp) -> None:
    """Keep only stock BeginPlay parent + one correct scope chain."""
    eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(sniper_bp))
    remove = []
    for node in eg.list_all_nodes():
        if node.get_class().get_name() == "K2Node_CustomEvent":
            remove.append(node)
    if remove:
        eg.remove_nodes(remove)
        log(f"Removed {len(remove)} custom events from EventGraph")

    # rebuild BeginPlay scope after parent
    nodes = {n.get_name(): n for n in eg.list_all_nodes()}
    begin = nodes.get("K2Node_Event_0")
    parent = nodes.get("K2Node_CallParentFunction_0")
    if not begin or not parent:
        return

    set_mesh = nodes.get("K2Node_CallFunction_0")
    set_vis = nodes.get("K2Node_CallFunction_1")
    if not set_mesh:
        set_mesh = eg.add_call_function_node(SET_STATIC_MESH_FN)
    if not set_vis:
        set_vis = eg.add_call_function_node(SET_VISIBILITY_FN)
    get_optic = nodes.get("K2Node_VariableGet_0") or eg.add_get_member_variable_node("OpticSight")
    get_scope = nodes.get("K2Node_VariableGet_1") or eg.add_get_member_variable_node("ScopeSightMesh")

    connect_data(output_pin(get_optic, "OpticSight"), set_mesh.find_input_pin("self"))
    connect_data(output_pin(get_scope, "ScopeSightMesh"), set_mesh.find_input_pin("NewMesh"))
    connect_data(output_pin(get_optic, "OpticSight"), set_vis.find_input_pin("self"))
    vis_pin = set_vis.find_input_pin("bNewVisibility")
    if vis_pin:
        vis_pin.set_pin_value("true")

    for pin in (
        begin.find_output_pin("then"),
        parent.find_output_pin("then"),
        set_mesh.find_input_pin("execute"),
        set_mesh.find_output_pin("then"),
        set_vis.find_input_pin("execute"),
    ):
        if pin:
            pin.break_pin_links()

    connect_exec(begin.find_output_pin("then"), parent.find_input_pin("execute"))
    connect_exec(parent.find_output_pin("then"), set_mesh.find_input_pin("execute"))
    connect_exec(set_mesh.find_output_pin("then"), set_vis.find_input_pin("execute"))
    log("EventGraph BeginPlay scope chain rebuilt")


def verify(sniper_bp, scope_mesh) -> None:
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    for handle in sds.k2_gather_subobject_data_for_blueprint(sniper_bp):
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(
            unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        )
        if obj and "OpticSight" in obj.get_name() and obj.get_class().get_name() == "StaticMeshComponent":
            sm = obj.get_editor_property("static_mesh")
            log(f"VERIFY template OpticSight={sm.get_name() if sm else None}")

    cls = sniper_bp.generated_class()
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(cls, unreal.Vector(0, 0, 1000), unreal.Rotator(0, 0, 0))
    optic = actor.get_editor_property("OpticSight")
    sm = optic.get_editor_property("static_mesh") if optic else None
    log(f"VERIFY spawned OpticSight={sm.get_name() if sm else None}")
    unreal.EditorLevelLibrary.destroy_actor(actor)


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    sniper_bp = unreal.load_asset(f"{SNIPER_BP}.BP_Weapon_Sniper")
    scope_mesh = unreal.load_asset(SCOPE_MESH)

    set_optic_template_mesh(sniper_bp, scope_mesh)
    ensure_ucs_scope(sniper_bp)
    clean_eventgraph_to_stock_plus_scope(sniper_bp)

    sniper_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(sniper_bp)
    unreal.EditorAssetLibrary.save_asset(SNIPER_BP, only_if_is_dirty=False)

    # Template mesh can reset during compile — re-apply and save again.
    set_optic_template_mesh(sniper_bp, scope_mesh)
    sniper_bp.modify()
    unreal.EditorAssetLibrary.save_asset(SNIPER_BP, only_if_is_dirty=False)

    verify(sniper_bp, scope_mesh)
    log("Done")


main()
