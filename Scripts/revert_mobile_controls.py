"""Remove mobile free-aim wiring; restore desktop Mouse X/Y -> FreeAim path."""
import unreal
from pathlib import Path

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/revert_mobile_controls.log")
RECOIL_NODE = "K2Node_CallFunction_153"
FREEAIM_NODE = "K2Node_CallFunction_23"
FREEAIM_TRANSFORM_SET = "K2Node_VariableSet_25"
MOUSE_X_NODE = "K2Node_GetInputAxisKeyValue_0"
MOUSE_Y_NODE = "K2Node_GetInputAxisKeyValue_1"

MOBILE_MARKERS = (
    "Mobile Left FreeAim Drag",
    "Mobile Left FreeAim Drag v2",
    "Mobile Left FreeAim Drag v3",
    "Mobile Left FreeAim Drag v4",
    "Mobile Left Zone FreeAim",
    "Mobile Left FreeAim Touch",
    "Mobile Left ADS Hold",
    "Mobile Left ADS Touch Events",
    "Mobile Touch Prev Exec",
    "Mobile Joystick FreeAim",
    "Mobile Joystick ADS Hold",
    "Mobile ADS FreeAim",
    "Mobile Touch Zones v",
    "Mobile Suppress LMB Shoot",
)

PROTECT = {
    MOUSE_X_NODE,
    MOUSE_Y_NODE,
    FREEAIM_NODE,
    FREEAIM_TRANSFORM_SET,
    "K2Node_CustomEvent_16",
    "K2Node_CustomEvent_19",
    "K2Node_EnhancedInputAction_9",
    "K2Node_IfThenElse_3",
    "K2Node_IfThenElse_23",
    "K2Node_CallFunction_56",
    "K2Node_CallFunction_379",
    "K2Node_CallFunction_153",
}


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[revert_mobile] {msg}")


def title(node) -> str:
    return str(node.get_node_title()).replace("\n", " | ")


def connect_exec(src, dst) -> None:
    if not src or not dst:
        raise RuntimeError("Missing exec pin")
    if not src.try_create_connection(dst):
        raise RuntimeError("Exec connection failed")


def connect_data(src, dst) -> None:
    if not src or not dst:
        raise RuntimeError("Missing data pin")
    if not src.try_create_connection(dst):
        raise RuntimeError("Data connection failed")


def find_node(editor, name: str):
    for node in editor.list_all_nodes():
        if node.get_name() == name:
            return node
    return None


def find_freeaim_node(editor):
    node = find_node(editor, FREEAIM_NODE)
    if node:
        return node
    for n in editor.list_all_nodes():
        if n.get_class().get_name() != "K2Node_CallFunction":
            continue
        if "FreeAim" in title(n):
            return n
    return None


def is_mobile_marker(node) -> bool:
    if node.get_class().get_name() != "K2Node_Comment":
        return False
    try:
        text = str(node.get_editor_property("node_comment"))
    except Exception:
        return False
    return any(m in text for m in MOBILE_MARKERS)


def collect_upstream_data_nodes(start_pins, protected_names):
    remove = set()
    stack = list(start_pins)
    while stack:
        pin = stack.pop()
        if not pin:
            continue
        node = unreal.BlueprintGraphPinLibrary.get_owning_node(pin)
        if not node:
            continue
        if node.get_name() in protected_names:
            continue
        if node in remove:
            continue
        remove.add(node)
        for candidate in unreal.BlueprintEditorLibrary.list_all_pins(node):
            for linked in unreal.BlueprintGraphPinLibrary.list_connected_pins(candidate):
                stack.append(linked)
    return remove


def cleanup_mobile_wiring(editor) -> None:
    remove = set()
    for node in editor.list_all_nodes():
        if is_mobile_marker(node):
            remove.add(node)
        if title(node) in ("Event BeginInputTouch", "Event EndInputTouch"):
            remove.add(node)
        if "GetInputTouchState" in title(node):
            remove.add(node)
        if "ContinuousInputInjectionForAction" in title(node):
            remove.add(node)

    stack = list(remove)
    while stack:
        n = stack.pop()
        if n.get_name() in PROTECT:
            continue
        remove.add(n)
        pins = []
        then_pin = n.find_then_pin()
        if then_pin:
            pins.append(then_pin)
        if n.get_class().get_name() == "K2Node_IfThenElse":
            else_pin = n.find_else_pin()
            if else_pin:
                pins.append(else_pin)
        for pin in pins:
            if not pin:
                continue
            for linked in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                n2 = unreal.BlueprintGraphPinLibrary.get_owning_node(linked)
                if n2 and n2.get_name() not in PROTECT and n2 not in remove:
                    stack.append(n2)

    if remove:
        editor.remove_nodes(list(remove))
        log(f"Removed {len(remove)} mobile wiring nodes")


def cleanup_freeaim_feed(editor, freeaim, mouse_x, mouse_y) -> None:
    protected = set(PROTECT) | {mouse_x.get_name(), mouse_y.get_name()}
    start_pins = []
    for pin_name in ("HorizontalMouse", "VerticalMouse"):
        pin = freeaim.find_input_pin(pin_name)
        if pin:
            start_pins.extend(unreal.BlueprintGraphPinLibrary.list_connected_pins(pin))
    remove = collect_upstream_data_nodes(start_pins, protected)
    for pin_name in ("HorizontalMouse", "VerticalMouse"):
        pin = freeaim.find_input_pin(pin_name)
        if pin:
            unreal.BlueprintGraphPinLibrary.break_pin_links(pin)
    if remove:
        editor.remove_nodes(list(remove))
        log(f"Removed {len(remove)} FreeAim feed nodes")


def restore_freeaim_exec(editor, freeaim) -> None:
    transform_set = find_node(editor, FREEAIM_TRANSFORM_SET)
    if not transform_set:
        return
    then = freeaim.find_then_pin()
    for linked in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
        owner = unreal.BlueprintGraphPinLibrary.get_owning_node(linked)
        if owner and owner.get_name() == transform_set.get_name():
            return
    unreal.BlueprintGraphPinLibrary.break_pin_links(then)
    connect_exec(then, transform_set.find_execute_pin())
    log("Restored FreeAim -> Set FreeAimTransform")


def restore_tick_recoil_only(editor) -> None:
    tick = editor.find_event_node("ReceiveTick")
    recoil = find_node(editor, RECOIL_NODE)
    if not tick or not recoil:
        raise RuntimeError("Missing ReceiveTick or Recoil")

    tick_then = tick.find_then_pin()
    links = list(unreal.BlueprintGraphPinLibrary.list_connected_pins(tick_then))
    for linked in links:
        owner = unreal.BlueprintGraphPinLibrary.get_owning_node(linked)
        if owner and owner.get_name() == RECOIL_NODE:
            log("ReceiveTick -> Recoil already direct")
            return
        if owner and "Sequence" in title(owner):
            pin0 = owner.find_output_pin("then_0")
            if pin0:
                for l2 in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin0):
                    n2 = unreal.BlueprintGraphPinLibrary.get_owning_node(l2)
                    if n2 and n2.get_name() == RECOIL_NODE:
                        log("ReceiveTick -> Sequence -> Recoil (tick branch removed by setup script)")
                        return

    unreal.BlueprintGraphPinLibrary.break_pin_links(tick_then)
    connect_exec(tick_then, recoil.find_execute_pin())
    log("Restored ReceiveTick -> Recoil only")


def restore_desktop_freeaim(editor) -> None:
    mouse_x = find_node(editor, MOUSE_X_NODE)
    mouse_y = find_node(editor, MOUSE_Y_NODE)
    freeaim = find_freeaim_node(editor)
    if not all((mouse_x, mouse_y, freeaim)):
        raise RuntimeError("Missing Mouse X/Y or FreeAimComponent")

    cleanup_freeaim_feed(editor, freeaim, mouse_x, mouse_y)
    connect_data(mouse_x.find_output_pin("ReturnValue"), freeaim.find_input_pin("HorizontalMouse"))
    connect_data(mouse_y.find_output_pin("ReturnValue"), freeaim.find_input_pin("VerticalMouse"))
    restore_freeaim_exec(editor, freeaim)
    log("Restored Get Mouse X/Y -> FreeAimComponent (desktop path)")


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()
    bp = unreal.load_asset(BP_ASSET)
    if not bp:
        raise RuntimeError(f"Missing {BP_ASSET}")
    eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)
    cleanup_mobile_wiring(editor)
    restore_desktop_freeaim(editor)
    restore_tick_recoil_only(editor)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)
    log("Done — reverted to 3-button touch interface + desktop FreeAim")


main()
