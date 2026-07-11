"""Wire EnsureWeaponLaserFlashEffects at end of AutomaticBase SpawnAttachments."""
import unreal
from pathlib import Path

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase"
BP_ASSET = f"{BP_PATH}.BP_Weapon_AutomaticBase"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_weapon_spawn_laser_effects.log")
ENSURE_FN = "/Script/SCAR.SCARWeaponAttachmentBlueprintLibrary:EnsureWeaponLaserFlashEffects"


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[fix_weapon_spawn_laser_effects] {msg}")


def find_node(editor, name: str):
    for node in editor.list_all_nodes():
        if node.get_name() == name:
            return node
    return None


def connect_exec(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def connect_data(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


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


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    bp = unreal.load_asset(BP_ASSET)
    if not bp:
        raise RuntimeError(f"Missing {BP_ASSET}")

    eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)

    if already_wired(editor):
        log("EnsureWeaponLaserFlashEffects already wired on AutomaticBase")
        return

    toggle_laser = find_node(editor, "K2Node_CallFunction_68") or find_node(editor, "K2Node_CallFunction_139")
    if not toggle_laser:
        raise RuntimeError("Could not find ToggleLaser node on AutomaticBase")

    ensure_node = editor.add_call_function_node(ENSURE_FN)
    if not ensure_node:
        raise RuntimeError("Failed creating EnsureWeaponLaserFlashEffects node")

    if not insert_exec_after_pin(toggle_laser.find_output_pin("then"), ensure_node):
        raise RuntimeError("Failed wiring ensure after ToggleLaser")

    self_node = editor.add_self_reference_node()
    connect_data(self_node.find_output_pin("self"), ensure_node.find_input_pin("Weapon"))

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)
    log("Wired EnsureWeaponLaserFlashEffects after ToggleLaser on AutomaticBase")


main()
