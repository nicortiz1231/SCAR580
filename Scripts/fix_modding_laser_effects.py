"""After UI_WeaponModding SpawnAttachments, call SCAR EnsureWeaponLaserFlashEffects."""
import unreal
from pathlib import Path

WBP_PATH = "/Game/BodycamFPSKIT/Blueprints/Widgets/UI_WeaponModding"
WBP_ASSET = f"{WBP_PATH}.UI_WeaponModding"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_modding_laser_effects.log")
ENSURE_FN = "/Script/SCAR.SCARWeaponAttachmentBlueprintLibrary:EnsureWeaponLaserFlashEffects"


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[fix_modding_laser_effects] {msg}")


def find_node(editor, name: str):
    for node in editor.list_all_nodes():
        if node.get_name() == name:
            return node
    return None


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


def insert_exec_after_pin(exec_out_pin, new_node) -> bool:
    if not exec_out_pin or not new_node:
        return False
    downstream = []
    for pin in exec_out_pin.list_connected_pins():
        if pin.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT:
            downstream.append(pin)
    exec_in = new_node.find_input_pin("execute")
    exec_out = new_node.find_output_pin("then")
    if not exec_in or not exec_out:
        return False
    if downstream:
        exec_out_pin.break_pin_links()
        if not connect_exec(exec_out_pin, exec_in):
            return False
        for pin in downstream:
            connect_exec(exec_out, pin)
        return True
    return connect_exec(exec_out_pin, exec_in)


def already_wired(editor) -> bool:
    for node in editor.list_all_nodes():
        if "EnsureWeaponLaserFlashEffects" in str(node.get_node_title()):
            return True
    return False


def wire_after_spawn(editor, spawn_node_name: str, weapon_getter_name: str) -> None:
    spawn_node = find_node(editor, spawn_node_name)
    getter = find_node(editor, weapon_getter_name)
    if not spawn_node or not getter:
        raise RuntimeError(f"Missing {spawn_node_name} or {weapon_getter_name}")

    ensure_node = editor.add_call_function_node(ENSURE_FN)
    if not ensure_node:
        raise RuntimeError("Failed creating EnsureWeaponLaserFlashEffects node")

    if not insert_exec_after_pin(spawn_node.find_output_pin("then"), ensure_node):
        raise RuntimeError(f"Failed wiring ensure after {spawn_node_name}")

    weapon_pin = None
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(getter):
        if str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin)) in ("Spawned Item", "ReturnValue"):
            weapon_pin = pin
            break
    if not weapon_pin:
        weapon_pin = output_pin(getter, "Spawned Item") or output_pin(getter, "ReturnValue")

    connect_data(weapon_pin, ensure_node.find_input_pin("Weapon"))
    log(f"Wired EnsureWeaponLaserFlashEffects after {spawn_node_name}")


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    wbp = unreal.load_asset(WBP_ASSET)
    if not wbp:
        raise RuntimeError(f"Missing {WBP_ASSET}")

    eg = unreal.BlueprintEditorLibrary.find_event_graph(wbp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)

    if already_wired(editor):
        log("EnsureWeaponLaserFlashEffects already wired")
        return

    wire_after_spawn(editor, "K2Node_CallFunction_24", "K2Node_VariableGet_4")
    wire_after_spawn(editor, "K2Node_CallFunction_36", "K2Node_VariableGet_4")

    unreal.BlueprintEditorLibrary.compile_blueprint(wbp)
    unreal.EditorAssetLibrary.save_asset(WBP_PATH, only_if_is_dirty=False)
    log("Saved UI_WeaponModding")


main()
