"""Bypass ToggleLaser calls on AutomaticBase and wire EnsureWeaponLaserFlashEffects."""
import unreal
from pathlib import Path

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase"
BP_ASSET = f"{BP_PATH}.BP_Weapon_AutomaticBase"
LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_laser_always_on.log")
ENSURE_FN = "/Script/SCAR.SCARWeaponAttachmentBlueprintLibrary:EnsureWeaponLaserFlashEffects"
TOGGLE_LASER_NODES = (
    "K2Node_CallFunction_68",
    "K2Node_CallFunction_139",
    "K2Node_CallFunction_141",
    "K2Node_CallFunction_106",
)


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[fix_laser_always_on] {msg}")


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


def bypass_toggle_laser(editor, toggle_node_name: str) -> None:
    toggle = find_node(editor, toggle_node_name)
    if not toggle:
        log(f"SKIP missing {toggle_node_name}")
        return

    exec_in = toggle.find_input_pin("execute")
    exec_out = toggle.find_output_pin("then")
    upstream_exec = None
    for pin in exec_in.list_connected_pins() if exec_in else []:
        if pin.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_OUTPUT:
            upstream_exec = pin
            break
    downstream_exec = []
    for pin in exec_out.list_connected_pins() if exec_out else []:
        if pin.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT:
            downstream_exec.append(pin)

    if upstream_exec and downstream_exec:
        exec_in.break_pin_links()
        for pin in downstream_exec:
            exec_out.break_pin_links()
            upstream_exec.try_create_connection(pin)
        log(f"Bypassed exec for {toggle_node_name}")
    else:
        log(f"SKIP bypass wiring for {toggle_node_name} (missing exec chain)")


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    bp = unreal.load_asset(BP_ASSET)
    eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)

    for node_name in TOGGLE_LASER_NODES:
        bypass_toggle_laser(editor, node_name)

    if not any("EnsureWeaponLaserFlashEffects" in str(n.get_node_title()) for n in editor.list_all_nodes()):
        ensure_node = editor.add_call_function_node(ENSURE_FN)
        anchor = (
            find_node(editor, "K2Node_CallFunction_139")
            or find_node(editor, "K2Node_CallFunction_68")
            or find_node(editor, "K2Node_CallFunction_138")
            or find_node(editor, "K2Node_CallFunction_67")
        )
        if ensure_node and anchor:
            if insert_exec_after_pin(anchor.find_output_pin("then"), ensure_node):
                self_node = None
                for node in editor.list_all_nodes():
                    if node.get_class().get_name() == "K2Node_Self":
                        self_node = node
                        break
                if self_node:
                    connect_data(self_node.find_output_pin("self"), ensure_node.find_input_pin("Weapon"))
                    log("Wired EnsureWeaponLaserFlashEffects on weapon")
                else:
                    log("Added EnsureWeaponLaserFlashEffects exec; SCARArLaserPresentationComponent covers Weapon pin")
            else:
                log("SKIP EnsureWeaponLaserFlashEffects exec wiring")
        else:
            log("SKIP EnsureWeaponLaserFlashEffects wiring (missing anchor node)")
    else:
        log("EnsureWeaponLaserFlashEffects already wired")

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)
    log("Saved AutomaticBase laser always-on patch")


main()
