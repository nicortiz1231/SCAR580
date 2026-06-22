"""Mobile ADS button + Bodycam free aim (hold ADS, drag to aim arms).

- Left TI control: button look, injects MouseX/MouseY while held+dragged.
- ADS: AIMOn/AIMOff on touch begin/end in the left ADS button area.
- Free aim: Get Mouse X/Y -> FreeAimComponent (identical to desktop).
"""
import unreal
from pathlib import Path

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/wire_mobile_ads_freeaim.log")
MARKER = "Mobile ADS FreeAim v5"
RECOIL_NODE = "K2Node_CallFunction_153"
FREEAIM_NODE = "K2Node_CallFunction_23"
FREEAIM_TRANSFORM_SET = "K2Node_VariableSet_25"
MOUSE_X_NODE = "K2Node_GetInputAxisKeyValue_0"
MOUSE_Y_NODE = "K2Node_GetInputAxisKeyValue_1"
AIM_ON_FN = "K2Node_CallFunction_56"
AIM_OFF_FN = "K2Node_CallFunction_379"

OLD_MARKERS = (
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
    MARKER,
)

WAS_PRESSED_VAR = "MobileAdsWasPressed"
ADS_HOLD_VAR = "MobileAdsTouchActive"

# Match create_mobile_touch_interface.py left ADS control.
LEFT_X = 0.17
VISUAL_SIZE = 0.22
INTERACTION_PAD = 0.08
LEFT_X_MIN = LEFT_X - (VISUAL_SIZE + INTERACTION_PAD) * 0.5
LEFT_X_MAX = LEFT_X + (VISUAL_SIZE + INTERACTION_PAD) * 0.5
BOTTOM_Y_MIN = 0.72

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
}


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[ads_freeaim] {msg}")


def title(node) -> str:
    return str(node.get_node_title()).replace("\n", " | ")


def pin_value(pin, value: str) -> None:
    if pin:
        pin.set_pin_value(value)


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


def var_output_pin(node, var_name: str):
    pin = node.find_output_pin(var_name)
    if pin:
        return pin
    for candidate in unreal.BlueprintEditorLibrary.list_all_pins(node):
        if unreal.BlueprintGraphPinLibrary.get_pin_direction(candidate) != unreal.EdGraphPinDirection.EGPD_OUTPUT:
            continue
        return candidate
    raise RuntimeError(f"Missing output pin on {var_name}")


def var_input_pin(node, var_name: str):
    pin = node.find_input_pin(var_name)
    if pin:
        return pin
    for candidate in unreal.BlueprintEditorLibrary.list_all_pins(node):
        if unreal.BlueprintGraphPinLibrary.get_pin_direction(candidate) != unreal.EdGraphPinDirection.EGPD_INPUT:
            continue
        if str(unreal.BlueprintGraphPinLibrary.get_pin_name(candidate)) in ("self", "execute"):
            continue
        return candidate
    raise RuntimeError(f"Missing input pin on {var_name}")


def divide(editor, a_pin, b_pin):
    node = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.Divide_DoubleDouble")
    connect_data(a_pin, node.find_input_pin("A"))
    connect_data(b_pin, node.find_input_pin("B"))
    return node.find_output_pin("ReturnValue")


def compare(editor, a_pin, b_pin, op: str):
    ops = {
        "lt": "/Script/Engine.KismetMathLibrary.Less_DoubleDouble",
        "le": "/Script/Engine.KismetMathLibrary.LessEqual_DoubleDouble",
        "ge": "/Script/Engine.KismetMathLibrary.GreaterEqual_DoubleDouble",
    }
    cmp_node = editor.add_call_function_node(ops[op])
    connect_data(a_pin, cmp_node.find_input_pin("A"))
    connect_data(b_pin, cmp_node.find_input_pin("B"))
    return cmp_node.find_output_pin("ReturnValue")


def compare_const(editor, a_pin, value: float, op: str):
    const = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble")
    pin_value(const.find_input_pin("A"), f"{value:.8f}")
    pin_value(const.find_input_pin("B"), "1.0")
    return compare(editor, a_pin, const.find_output_pin("ReturnValue"), op)


def bool_not(editor, a_pin):
    node = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.Not_PreBool")
    connect_data(a_pin, node.find_input_pin("A"))
    return node.find_output_pin("ReturnValue")


def bool_and(editor, a_pin, b_pin):
    node = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.BooleanAND")
    connect_data(a_pin, node.find_input_pin("A"))
    connect_data(b_pin, node.find_input_pin("B"))
    return node.find_output_pin("ReturnValue")


def bool_or(editor, a_pin, b_pin):
    node = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.BooleanOR")
    connect_data(a_pin, node.find_input_pin("A"))
    connect_data(b_pin, node.find_input_pin("B"))
    return node.find_output_pin("ReturnValue")


def is_marker(node, markers) -> bool:
    if node.get_class().get_name() != "K2Node_Comment":
        return False
    try:
        text = str(node.get_editor_property("node_comment"))
    except Exception:
        return False
    return any(m in text for m in markers)


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


def cleanup_old_wiring(editor) -> None:
    remove = set()
    for node in editor.list_all_nodes():
        if is_marker(node, OLD_MARKERS):
            remove.add(node)

    stack = list(remove)
    while stack:
        n = stack.pop()
        if n.get_name() in PROTECT:
            continue
        remove.add(n)
        for pin in (n.find_then_pin(), n.find_else_pin()):
            if not pin:
                continue
            for linked in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                n2 = unreal.BlueprintGraphPinLibrary.get_owning_node(linked)
                if n2 and n2.get_name() not in PROTECT and n2 not in remove:
                    stack.append(n2)

    if remove:
        editor.remove_nodes(list(remove))
        log(f"Removed {len(remove)} old mobile wiring nodes")


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
        log(f"Removed {len(remove)} old FreeAim feed nodes")


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


def _exec_out_pins(node):
    pins = []
    then_pin = node.find_then_pin()
    if then_pin:
        pins.append(then_pin)
    if node.get_class().get_name() == "K2Node_IfThenElse":
        else_pin = node.find_else_pin()
        if else_pin:
            pins.append(else_pin)
    if node.get_class().get_name() == "K2Node_ExecutionSequence":
        for candidate in unreal.BlueprintEditorLibrary.list_all_pins(node):
            if unreal.BlueprintGraphPinLibrary.get_pin_direction(candidate) != unreal.EdGraphPinDirection.EGPD_OUTPUT:
                continue
            if str(unreal.BlueprintGraphPinLibrary.get_pin_name(candidate)).startswith("then_"):
                pins.append(candidate)
    return pins


def exec_chain_reaches_from_tick(editor, tick, target_name: str, max_depth: int = 48) -> bool:
    start = tick.find_then_pin()
    if not start:
        return False
    stack = [(start, 0)]
    visited = set()
    while stack:
        pin, depth = stack.pop()
        if depth > max_depth:
            continue
        if id(pin) in visited:
            continue
        visited.add(id(pin))
        for linked in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            node = unreal.BlueprintGraphPinLibrary.get_owning_node(linked)
            if not node:
                continue
            if node.get_name() == target_name:
                return True
            for out_pin in _exec_out_pins(node):
                stack.append((out_pin, depth + 1))
    return False


def ensure_tick_recoil(editor) -> None:
    tick = editor.find_event_node("ReceiveTick")
    recoil = find_node(editor, RECOIL_NODE)
    if not tick or not recoil:
        raise RuntimeError("Missing ReceiveTick or Recoil")
    if exec_chain_reaches_from_tick(editor, tick, RECOIL_NODE):
        log("ReceiveTick already reaches Recoil")
        return
    tick_then = tick.find_then_pin()
    existing = list(unreal.BlueprintGraphPinLibrary.list_connected_pins(tick_then))
    if existing:
        seq = editor.create_node_from_name(
            "Utilities|FlowControl|Sequence",
            unreal.Vector2D(tick.get_node_pos().x + 200, tick.get_node_pos().y),
            [],
        )
        unreal.BlueprintGraphPinLibrary.break_pin_links(tick_then)
        connect_exec(tick_then, seq.find_execute_pin())
        connect_exec(seq.find_output_pin("then_0"), recoil.find_execute_pin())
        connect_exec(seq.find_output_pin("then_1"), existing[0])
        log("Inserted Sequence: ReceiveTick -> Recoil + existing branch")
        return
    unreal.BlueprintGraphPinLibrary.break_pin_links(tick_then)
    connect_exec(tick_then, recoil.find_execute_pin())
    log("Restored ReceiveTick -> Recoil")


def ensure_member_vars(editor, bp) -> None:
    names = set(unreal.BlueprintEditorLibrary.list_member_variable_names(bp))
    bool_type = unreal.BlueprintEditorLibrary.get_member_variable_type(bp, "IsAim")
    for var_name in (WAS_PRESSED_VAR, ADS_HOLD_VAR):
        if var_name not in names:
            editor.add_member_variable(var_name, bool_type)
            log(f"Added bool member {var_name}")


def find_ads_tick_entry(editor):
    tick = editor.find_event_node("ReceiveTick")
    if not tick:
        return None, None
    tick_then = tick.find_then_pin()
    for linked in unreal.BlueprintGraphPinLibrary.list_connected_pins(tick_then):
        node = unreal.BlueprintGraphPinLibrary.get_owning_node(linked)
        if not node:
            continue
        if node.get_class().get_name() == "K2Node_ExecutionSequence":
            for pin_name in ("then_1", "then_2"):
                pin = node.find_output_pin(pin_name)
                if pin:
                    links = unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)
                    marker = is_marker(node, (MARKER,))
                    if not links or marker:
                        return pin, node
        if node.get_name() == RECOIL_NODE:
            seq = editor.create_node_from_name(
                "Utilities|FlowControl|Sequence",
                unreal.Vector2D(tick.get_node_pos().x + 180, tick.get_node_pos().y),
                [],
            )
            unreal.BlueprintGraphPinLibrary.break_pin_links(tick_then)
            connect_exec(tick_then, seq.find_execute_pin())
            connect_exec(seq.find_output_pin("then_0"), linked)
            return seq.find_output_pin("then_1"), seq
    return None, None


def wire_direct_mouse_to_freeaim(editor, freeaim, mouse_x, mouse_y) -> None:
    connect_data(mouse_x.find_output_pin("ReturnValue"), freeaim.find_input_pin("HorizontalMouse"))
    connect_data(mouse_y.find_output_pin("ReturnValue"), freeaim.find_input_pin("VerticalMouse"))
    log("Wired Get Mouse X/Y -> FreeAimComponent")


def wire_mobile_ads_shift(editor, bp) -> None:
    entry_pin, seq = find_ads_tick_entry(editor)
    if not entry_pin:
        raise RuntimeError("Could not find tick branch for mobile ADS")

    aim_on = find_node(editor, AIM_ON_FN)
    aim_off = find_node(editor, AIM_OFF_FN)
    if not aim_on or not aim_off:
        raise RuntimeError("Missing AIMOn/AIMOff nodes")

    ensure_member_vars(editor, bp)

    get_pc = editor.add_call_function_node("/Script/Engine.GameplayStatics.GetPlayerController")
    get_touch = editor.add_call_function_node("/Script/Engine.PlayerController.GetInputTouchState")
    get_viewport = editor.add_call_function_node("/Script/UMG.WidgetLayoutLibrary.GetViewportSize")
    break_vec = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.BreakVector2D")
    get_was = editor.add_get_member_variable_node(WAS_PRESSED_VAR)
    set_was = editor.add_set_member_variable_node(WAS_PRESSED_VAR)
    get_hold = editor.add_get_member_variable_node(ADS_HOLD_VAR)
    set_hold_true = editor.add_set_member_variable_node(ADS_HOLD_VAR)
    set_hold_false = editor.add_set_member_variable_node(ADS_HOLD_VAR)

    pin_value(get_pc.find_input_pin("PlayerIndex"), "0")
    pin_value(get_pc.find_input_pin("WorldContextObject"), "self")
    pin_value(get_viewport.find_input_pin("WorldContextObject"), "self")
    pin_value(get_touch.find_input_pin("FingerIndex"), "0")

    connect_data(get_pc.find_output_pin("ReturnValue"), get_touch.find_input_pin("self"))
    connect_data(get_viewport.find_output_pin("ReturnValue"), break_vec.find_input_pin("InVec"))

    norm_x = divide(editor, get_touch.find_output_pin("LocationX"), break_vec.find_output_pin("X"))
    norm_y = divide(editor, get_touch.find_output_pin("LocationY"), break_vec.find_output_pin("Y"))
    pressed = get_touch.find_output_pin("bIsCurrentlyPressed")

    in_left = bool_and(
        editor,
        compare_const(editor, norm_x, LEFT_X_MIN, "ge"),
        compare_const(editor, norm_x, LEFT_X_MAX, "le"),
    )
    in_bottom = compare_const(editor, norm_y, BOTTOM_Y_MIN, "ge")
    in_ads_box = bool_and(editor, in_left, in_bottom)

    was_pressed = var_output_pin(get_was, WAS_PRESSED_VAR)
    touch_rising = bool_and(editor, pressed, bool_not(editor, was_pressed))
    touch_falling = bool_and(editor, bool_not(editor, pressed), was_pressed)

    ads_touch_start = bool_and(editor, in_ads_box, touch_rising)
    ads_touch_end = bool_and(editor, var_output_pin(get_hold, ADS_HOLD_VAR), touch_falling)

    branch_start = editor.add_branch_node()
    branch_end = editor.add_branch_node()
    connect_data(ads_touch_start, branch_start.find_input_pin("Condition"))
    connect_data(ads_touch_end, branch_end.find_input_pin("Condition"))

    pin_value(var_input_pin(set_hold_true, ADS_HOLD_VAR), "true")
    pin_value(var_input_pin(set_hold_false, ADS_HOLD_VAR), "false")

    connect_exec(entry_pin, branch_start.find_execute_pin())
    connect_exec(branch_start.find_then_pin(), aim_on.find_execute_pin())
    connect_exec(aim_on.find_then_pin(), set_hold_true.find_execute_pin())
    connect_exec(set_hold_true.find_then_pin(), branch_end.find_execute_pin())
    connect_exec(branch_start.find_else_pin(), branch_end.find_execute_pin())

    connect_exec(branch_end.find_then_pin(), aim_off.find_execute_pin())
    connect_exec(aim_off.find_then_pin(), set_hold_false.find_execute_pin())
    connect_exec(set_hold_false.find_then_pin(), set_was.find_execute_pin())
    connect_exec(branch_end.find_else_pin(), set_was.find_execute_pin())
    connect_data(pressed, var_input_pin(set_was, WAS_PRESSED_VAR))

    pos = seq.get_node_pos() if seq else unreal.Vector2D(0, 0)
    editor.add_comment_node(MARKER, unreal.Vector2D(pos.x + 60, pos.y + 480), unreal.Vector2D(1200, 560))
    log("Wired tick ADS: AIMOn/AIMOff on left ADS touch begin/end")


def wire_ads_freeaim(editor, bp) -> None:
    mouse_x = find_node(editor, MOUSE_X_NODE)
    mouse_y = find_node(editor, MOUSE_Y_NODE)
    freeaim = find_freeaim_node(editor)
    if not all((mouse_x, mouse_y, freeaim)):
        raise RuntimeError("Missing Mouse X/Y or FreeAimComponent")

    cleanup_freeaim_feed(editor, freeaim, mouse_x, mouse_y)
    restore_freeaim_exec(editor, freeaim)
    wire_direct_mouse_to_freeaim(editor, freeaim, mouse_x, mouse_y)
    wire_mobile_ads_shift(editor, bp)


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()
    bp = unreal.load_asset(BP_ASSET)
    if not bp:
        raise RuntimeError(f"Missing {BP_ASSET}")
    eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)
    cleanup_old_wiring(editor)
    ensure_tick_recoil(editor)
    wire_ads_freeaim(editor, bp)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)
    log("Done — ADS button + MouseX/Y drag -> FreeAim (Bodycam path)")


main()
