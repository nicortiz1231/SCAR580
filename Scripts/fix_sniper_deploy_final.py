"""CDO default scope mesh + character applies SetStaticMesh after sniper spawn."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_sniper_deploy_final.log")
CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
SNIPER_BP = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper"
ITEM_BP = "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base"
SCOPE_MESH = "/Game/BodycamFPSKIT/Demo/Meshes/SM_4xScopeForSniper.SM_4xScopeForSniper"
SET_STATIC_MESH_FN = "/Script/Engine.StaticMeshComponent:SetStaticMesh"
SET_VISIBILITY_FN = "/Script/Engine.SceneComponent:SetVisibility"
SPAWN_ATT = "K2Node_CallFunction_141"
VAR_GET_NEXT = "K2Node_VariableGet_83"
SPAWNED_GET = "K2Node_VariableGet_192"


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[deploy_final] {msg}")


def connect_exec(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def connect_data(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def find_node(editor, name: str):
    for node in editor.list_all_nodes():
        if node.get_name() == name:
            return node
    return None


def set_sniper_cdo_optic(sniper_bp, scope_mesh) -> None:
    cdo = unreal.get_default_object(sniper_bp.generated_class())
    optic = cdo.get_editor_property("OpticSight")
    if optic:
        optic.set_static_mesh(scope_mesh)
        optic.set_visibility(True, False)
        optic.set_hidden_in_game(False)
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    for handle in sds.k2_gather_subobject_data_for_blueprint(sniper_bp):
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(
            unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        )
        if obj and "OpticSight" in obj.get_name() and obj.get_class().get_name() == "StaticMeshComponent":
            obj.set_editor_property("static_mesh", scope_mesh)
            obj.set_editor_property("hidden_in_game", False)


def cleanup_sniper_duplicates(sniper_bp) -> None:
    eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(sniper_bp))
    remove = []
    for node in eg.list_all_nodes():
        if node.get_class().get_name() == "K2Node_CustomEvent":
            remove.append(node)
        if node.get_class().get_name() == "K2Node_CallFunction":
            t = str(node.get_node_title())
            if ("SetStaticMesh" in t or "SetVisibility" in t) and node.get_name() not in ("K2Node_CallFunction_0", "K2Node_CallFunction_1"):
                remove.append(node)
        if node.get_class().get_name() == "K2Node_VariableGet" and node.get_name() not in ("K2Node_VariableGet_0", "K2Node_VariableGet_1"):
            t = str(node.get_node_title())
            if "OpticSight" in t or "ScopeSight" in t:
                remove.append(node)
    if remove:
        eg.remove_nodes(list({id(n): n for n in remove}.values()))
        log(f"Cleaned {len(remove)} duplicate sniper nodes")


def char_scope_already_wired(editor) -> bool:
    spawn_att = find_node(editor, SPAWN_ATT)
    if not spawn_att:
        return False
    then = spawn_att.find_output_pin("then")
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
        if "SetStaticMesh" in str(lp.get_owning_node().get_node_title()):
            return True
    return False


def wire_char_scope_on_spawn(char_bp, scope_mesh) -> None:
    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
    )
    if char_scope_already_wired(editor):
        log("Character scope chain already wired")
        return

    spawn_att = find_node(editor, SPAWN_ATT)
    var_get_next = find_node(editor, VAR_GET_NEXT)
    spawned_get = find_node(editor, SPAWNED_GET)
    if not all((spawn_att, var_get_next, spawned_get)):
        raise RuntimeError("Missing sniper spawn nodes on character")

    set_mesh = editor.add_call_function_node(SET_STATIC_MESH_FN)
    set_vis = editor.add_call_function_node(SET_VISIBILITY_FN)
    if not set_mesh or not set_vis:
        raise RuntimeError("Failed to create SetStaticMesh nodes")

    # OpticSight lives on the weapon (SpawnedItem), not on the character.
    item_cls = unreal.load_asset(f"{ITEM_BP}.BP_Item_Base").generated_class()
    get_optic = editor.add_get_member_variable_node("OpticSight", target_class=item_cls)
    if not get_optic:
        get_optic = editor.add_get_member_variable_node("OpticSight")

    spawned_pin = spawned_get.find_output_pin("SpawnedItem")
    if not spawned_pin:
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(spawned_get):
            if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) == unreal.EdGraphPinDirection.EGPD_OUTPUT:
                pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                if "SpawnedItem" in pname or pname == "SpawnedItem":
                    spawned_pin = pin
                    break

    connect_data(spawned_pin, get_optic.find_input_pin("self"))
    connect_data(get_optic.find_output_pin("OpticSight"), set_mesh.find_input_pin("self"))
    connect_data(get_optic.find_output_pin("OpticSight"), set_vis.find_input_pin("self"))

    mesh_pin = set_mesh.find_input_pin("NewMesh")
    if mesh_pin:
        mesh_pin.set_pin_value(SCOPE_MESH)
    vis_pin = set_vis.find_input_pin("bNewVisibility")
    if vis_pin:
        vis_pin.set_pin_value("true")

    spawn_then = spawn_att.find_output_pin("then")
    next_exec = var_get_next.find_input_pin("execute")
    spawn_then.break_pin_links()
    connect_exec(spawn_then, set_mesh.find_input_pin("execute"))
    connect_exec(set_mesh.find_output_pin("then"), set_vis.find_input_pin("execute"))
    connect_exec(set_vis.find_output_pin("then"), next_exec)
    log("Wired character: sniper SpawnAttachments -> SetStaticMesh(4x scope) -> SetVisibility")


def verify_spawn(sniper_bp) -> None:
    cdo = unreal.get_default_object(sniper_bp.generated_class())
    optic = cdo.get_editor_property("OpticSight")
    sm = optic.get_static_mesh() if optic else None
    log(f"VERIFY CDO OpticSight mesh={sm.get_name() if sm else 'NONE'}")

    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        sniper_bp.generated_class(), unreal.Vector(0, 0, 3000), unreal.Rotator(0, 0, 0)
    )
    o = actor.get_editor_property("OpticSight")
    sm2 = o.get_static_mesh() if o else None
    log(f"VERIFY spawned OpticSight mesh={sm2.get_name() if sm2 else 'NONE'}")
    unreal.EditorLevelLibrary.destroy_actor(actor)


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    scope_mesh = unreal.load_asset(SCOPE_MESH)
    sniper_bp = unreal.load_asset(f"{SNIPER_BP}.BP_Weapon_Sniper")
    char_bp = unreal.load_asset(f"{CHAR_BP}.BP_FPCharacter")

    cleanup_sniper_duplicates(sniper_bp)
    set_sniper_cdo_optic(sniper_bp, scope_mesh)
    wire_char_scope_on_spawn(char_bp, scope_mesh)

    for bp, path in ((sniper_bp, SNIPER_BP), (char_bp, CHAR_BP)):
        bp.modify()
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)

    set_sniper_cdo_optic(sniper_bp, scope_mesh)
    sniper_bp.modify()
    unreal.EditorAssetLibrary.save_asset(SNIPER_BP, only_if_is_dirty=False)

    verify_spawn(sniper_bp)
    log("Done")


main()
