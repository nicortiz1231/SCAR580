"""Hide weapon OpticSight mesh during sniper scope ADS; show on ADS off."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_sniper_hide_optic_ads.log")
CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
ITEM_CLASS = "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base_C"
SET_VIS_FN = "/Script/Engine.SceneComponent:SetVisibility"
AIM_ON_AFTER = "K2Node_CallFunction_128"
AIM_OFF_AFTER = "K2Node_CallFunction_144"


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[hide_optic_ads] {msg}")


def find_node(editor, name: str):
    for node in editor.list_all_nodes():
        if node.get_name() == name:
            return node
    return None


def find_spawned_item_get(editor):
    for node in editor.list_all_nodes():
        if node.get_class().get_name() != "K2Node_VariableGet":
            continue
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            if str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin)) == "SpawnedItem":
                return node
    return None


def connect_exec(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def connect_data(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def already_wired(editor, after_name: str, visible: bool) -> bool:
    after = find_node(editor, after_name)
    if not after:
        return False
    then = after.find_output_pin("then")
    if not then:
        return False
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
        n = lp.get_owning_node()
        if "SetVisibility" not in str(n.get_node_title()):
            continue
        vis = n.find_input_pin("bNewVisibility")
        if vis and str(unreal.BlueprintGraphPinLibrary.get_pin_value(vis) or "").lower() == str(visible).lower():
            return True
    return False


def insert_optic_visibility(editor, after_name: str, visible: bool, label: str) -> None:
    if already_wired(editor, after_name, visible):
        log(f"{label} optic visibility already wired -> {visible}")
        return

    after = find_node(editor, after_name)
    spawned_get = find_spawned_item_get(editor)
    if not after or not spawned_get:
        raise RuntimeError(f"Missing nodes for {label}: after={bool(after)} spawned={bool(spawned_get)}")

    then = after.find_output_pin("then")
    spawned_pin = spawned_get.find_output_pin("SpawnedItem")
    if not then or not spawned_pin:
        raise RuntimeError(f"Missing pins for {label}")

    set_vis = editor.add_call_function_node(SET_VIS_FN)
    get_optic = editor.add_get_member_variable_node("OpticSight", ITEM_CLASS)
    if not set_vis or not get_optic:
        raise RuntimeError(f"Failed creating nodes for {label}")

    connect_data(spawned_pin, get_optic.find_input_pin("self"))
    connect_data(get_optic.find_output_pin("OpticSight"), set_vis.find_input_pin("self"))
    vis_pin = set_vis.find_input_pin("bNewVisibility")
    if vis_pin:
        vis_pin.set_pin_value("true" if visible else "false")
    prop_pin = set_vis.find_input_pin("bPropagateToChildren")
    if prop_pin:
        prop_pin.set_pin_value("false")

    downstream = list(unreal.BlueprintGraphPinLibrary.list_connected_pins(then))
    then.break_pin_links()
    connect_exec(then, set_vis.find_input_pin("execute"))
    set_then = set_vis.find_output_pin("then")
    for pin in downstream:
        connect_exec(set_then, pin)
    log(f"Wired {after_name} -> SpawnedItem.OpticSight SetVisibility({visible})")


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    char_bp = unreal.load_asset(f"{CHAR_BP}.BP_FPCharacter")
    if not char_bp:
        raise RuntimeError("Missing BP_FPCharacter")

    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
    )
    insert_optic_visibility(editor, AIM_ON_AFTER, False, "AIMOn")
    insert_optic_visibility(editor, AIM_OFF_AFTER, True, "AIMOff")

    char_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(char_bp)
    unreal.EditorAssetLibrary.save_asset(CHAR_BP, only_if_is_dirty=False)
    log("Done")


main()
