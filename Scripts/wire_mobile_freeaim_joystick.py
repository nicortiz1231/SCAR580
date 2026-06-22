"""Mobile free aim via TouchInterface joystick -> MouseX/Y (desktop path).

Left control is a virtual stick injecting MouseX/MouseY while held. ADS is driven on
tick from touch begin/end in the left zone (AIMOn/AIMOff) because the stick no longer
sends LeftShift.
"""
import unreal
from pathlib import Path

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/wire_mobile_freeaim_joystick.log")
MARKER = "Mobile Joystick FreeAim v1"
ADS_MARKER = "Mobile Joystick ADS Hold"
RECOIL_NODE = "K2Node_CallFunction_153"
FREEAIM_NODE = "K2Node_CallFunction_23"
FREEAIM_TRANSFORM_SET = "K2Node_VariableSet_25"
MOUSE_X_NODE = "K2Node_GetInputAxisKeyValue_0"
MOUSE_Y_NODE = "K2Node_GetInputAxisKeyValue_1"
AIM_ON_FN = "K2Node_CallFunction_56"
AIM_OFF_FN = "K2Node_CallFunction_379"
WAS_PRESSED_VAR = "MobileAdsWasPressed"

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
    MARKER,
    ADS_MARKER,
)

# Bottom-half left third (matches left joystick placement).
BOTTOM_FRAC = 0.50
LEFT_X_FRAC = 0.333333

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
    AIM_ON_FN,
    AIM_OFF_FN,
}


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[freeaim_joystick] {msg}")


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


def compare_const(editor, a_pin, value: float, op: str):
    ops = {
        "lt": "/Script/Engine.KismetMathLibrary.Less_DoubleDouble",
        "ge": "/Script/Engine.KismetMathLibrary.GreaterEqual_DoubleDouble",
    }
    const = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble")
    pin_value(const.find_input_pin("A"), f"{value:.8f}")
    pin_value(const.find_input_pin("B"), "1.0")
    cmp_node = editor.add_call_function_node(ops[op])
    connect_data(a_pin, cmp_node.find_input_pin("A"))
    connect_data(const.find_output_pin("ReturnValue"), cmp_node.find_input_pin("B"))
    return cmp_node.find_output_pin("ReturnValue")


def bool_not(editor, a_pin):
    node = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.Not_PreBool")
    connect_data(a_pin, node.find_input_pin("A"))
    return node.find_output_pin("ReturnValue")


def bool_and(editor, a_pin, b_pin):
    node = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.BooleanAND")
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
        name = node.get_name()
        if name in protected_names:
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


def cleanup_freeaim_touch_feed(editor, freeaim, mouse_x, mouse_y) -> None:
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
        log(f"Removed {len(remove)} touch-delta feed nodes")


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
    log("Restored FreeAim -> Set FreeAimTransform exec")


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
        pin_id = id(pin)
        if pin_id in visited:
            continue
        visited.add(pin_id)
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
        raise RuntimeError("Missing ReceiveTick or Recoil node")
    if exec_chain_reaches_from_tick(editor, tick, RECOIL_NODE):
        log("ReceiveTick already reaches Recoil")
        return
    tick_then = tick.find_then_pin()
    existing = list(unreal.BlueprintGraphPinLibrary.list_connected_pins(tick_then))
    tick_pos = tick.get_node_pos()
    if existing:
        seq = editor.create_node_from_name(
            "Utilities|FlowControl|Sequence",
            unreal.Vector2D(tick_pos.x + 200, tick_pos.y),
            [],
        )
        if not seq:
            raise RuntimeError("Could not create Sequence for ReceiveTick")
        unreal.BlueprintGraphPinLibrary.break_pin_links(tick_then)
        connect_exec(tick_then, seq.find_execute_pin())
        connect_exec(seq.find_output_pin("then_0"), recoil.find_execute_pin())
        connect_exec(seq.find_output_pin("then_1"), existing[0])
        log("Inserted Sequence: ReceiveTick -> Recoil + existing branch")
        return
    unreal.BlueprintGraphPinLibrary.break_pin_links(tick_then)
    connect_exec(tick_then, recoil.find_execute_pin())
    log("Restored ReceiveTick -> Recoil")


def ensure_was_pressed_var(editor, bp) -> None:
    names = set(unreal.BlueprintEditorLibrary.list_member_variable_names(bp))
    if WAS_PRESSED_VAR in names:
        return
    bool_type = unreal.BlueprintEditorLibrary.get_member_variable_type(bp, "IsAim")
    editor.add_member_variable(WAS_PRESSED_VAR, bool_type)
    log(f"Added bool member {WAS_PRESSED_VAR}")


def wire_direct_mouse_to_freeaim(editor, freeaim, mouse_x, mouse_y) -> None:
    h_pin = freeaim.find_input_pin("HorizontalMouse")
    v_pin = freeaim.find_input_pin("VerticalMouse")
    if not h_pin or not v_pin:
        raise RuntimeError("FreeAimComponent missing HorizontalMouse/VerticalMouse")
    connect_data(mouse_x.find_output_pin("ReturnValue"), h_pin)
    connect_data(mouse_y.find_output_pin("ReturnValue"), v_pin)
    log("Wired Get Mouse X/Y -> FreeAimComponent (same path as laptop)")


def wire_branch(branch, true_exec, next_exec) -> None:
    then_pin = branch.find_then_pin()
    else_pin = branch.find_else_pin()
    if true_exec:
        connect_exec(then_pin, true_exec)
        true_node = unreal.BlueprintGraphPinLibrary.get_owning_node(true_exec)
        if true_node:
            out = true_node.find_then_pin()
            if out:
                connect_exec(out, next_exec)
    connect_exec(else_pin, next_exec)


def find_ads_tick_entry(editor):
    """Return exec pin we can chain mobile ADS logic from (parallel to Recoil)."""
    tick = editor.find_event_node("ReceiveTick")
    if not tick:
        return None, None
    tick_then = tick.find_then_pin()
    for linked in unreal.BlueprintGraphPinLibrary.list_connected_pins(tick_then):
        node = unreal.BlueprintGraphPinLibrary.get_owning_node(linked)
        if not node:
            continue
        if node.get_class().get_name() == "K2Node_ExecutionSequence":
            pin1 = node.find_output_pin("then_1")
            if pin1 and not unreal.BlueprintGraphPinLibrary.list_connected_pins(pin1):
                return pin1, node
            pin2 = node.find_output_pin("then_2")
            if pin2 and not unreal.BlueprintGraphPinLibrary.list_connected_pins(pin2):
                return pin2, node
        if node.get_name() == RECOIL_NODE:
            tick_pos = tick.get_node_pos()
            seq = editor.create_node_from_name(
                "Utilities|FlowControl|Sequence",
                unreal.Vector2D(tick_pos.x + 180, tick_pos.y),
                [],
            )
            if not seq:
                raise RuntimeError("Could not create tick Sequence for ADS")
            unreal.BlueprintGraphPinLibrary.break_pin_links(tick_then)
            connect_exec(tick_then, seq.find_execute_pin())
            connect_exec(seq.find_output_pin("then_0"), linked)
            return seq.find_output_pin("then_1"), seq
    return None, None


def wire_mobile_ads_hold(editor, bp) -> None:
    aim_on = find_node(editor, AIM_ON_FN)
    aim_off = find_node(editor, AIM_OFF_FN)
    if not aim_on or not aim_off:
        raise RuntimeError("Missing AIMOn/AIMOff nodes")

    entry_pin, seq = find_ads_tick_entry(editor)
    if not entry_pin:
        log("WARN: Could not find parallel tick slot for ADS — skipping")
        return

    ensure_was_pressed_var(editor, bp)

    get_pc = editor.add_call_function_node("/Script/Engine.GameplayStatics.GetPlayerController")
    get_touch = editor.add_call_function_node("/Script/Engine.PlayerController.GetInputTouchState")
    get_viewport = editor.add_call_function_node("/Script/UMG.WidgetLayoutLibrary.GetViewportSize")
    break_vec = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.BreakVector2D")
    get_was = editor.add_get_member_variable_node(WAS_PRESSED_VAR)
    set_was = editor.add_set_member_variable_node(WAS_PRESSED_VAR)
    get_aim = editor.add_get_member_variable_node("IsAim")

    pin_value(get_pc.find_input_pin("PlayerIndex"), "0")
    pin_value(get_pc.find_input_pin("WorldContextObject"), "self")
    pin_value(get_viewport.find_input_pin("WorldContextObject"), "self")
    pin_value(get_touch.find_input_pin("FingerIndex"), "0")

    connect_data(get_pc.find_output_pin("ReturnValue"), get_touch.find_input_pin("self"))
    connect_data(get_viewport.find_output_pin("ReturnValue"), break_vec.find_input_pin("InVec"))

    norm_x = divide(editor, get_touch.find_output_pin("LocationX"), break_vec.find_output_pin("X"))
    norm_y = divide(editor, get_touch.find_output_pin("LocationY"), break_vec.find_output_pin("Y"))
    pressed = get_touch.find_output_pin("bIsCurrentlyPressed")

    strip_top = 1.0 - BOTTOM_FRAC
    in_strip = compare_const(editor, norm_y, strip_top, "ge")
    in_left = compare_const(editor, norm_x, LEFT_X_FRAC, "lt")
    bottom_left = bool_and(editor, in_strip, in_left)

    was_pressed = var_output_pin(get_was, WAS_PRESSED_VAR)
    touch_rising = bool_and(editor, pressed, bool_not(editor, was_pressed))
    touch_falling = bool_and(editor, bool_not(editor, pressed), was_pressed)

    aim_start = bool_and(editor, bottom_left, touch_rising)
    aim_stop = bool_and(editor, var_output_pin(get_aim, "IsAim"), touch_falling)

    branch_on = editor.add_branch_node()
    branch_off = editor.add_branch_node()
    connect_data(aim_start, branch_on.find_input_pin("Condition"))
    connect_data(aim_stop, branch_off.find_input_pin("Condition"))

    connect_exec(entry_pin, branch_on.find_execute_pin())
    wire_branch(branch_on, aim_on.find_execute_pin(), branch_off.find_execute_pin())
    wire_branch(branch_off, aim_off.find_execute_pin(), set_was.find_execute_pin())
    connect_data(pressed, var_input_pin(set_was, WAS_PRESSED_VAR))

    pos = seq.get_node_pos() if seq else unreal.Vector2D(0, 0)
    editor.add_comment_node(
        ADS_MARKER,
        unreal.Vector2D(pos.x + 80, pos.y + 520),
        unreal.Vector2D(1100, 520),
    )
    log("Wired tick ADS: touch begin in left zone -> AIMOn, release -> AIMOff")


def wire_freeaim_joystick(editor, bp) -> None:
    mouse_x = find_node(editor, MOUSE_X_NODE)
    mouse_y = find_node(editor, MOUSE_Y_NODE)
    freeaim = find_freeaim_node(editor)
    if not all((mouse_x, mouse_y, freeaim)):
        raise RuntimeError("Missing Mouse X/Y or FreeAimComponent nodes")

    cleanup_freeaim_touch_feed(editor, freeaim, mouse_x, mouse_y)
    restore_freeaim_exec(editor, freeaim)
    wire_direct_mouse_to_freeaim(editor, freeaim, mouse_x, mouse_y)
    wire_mobile_ads_hold(editor, bp)

    tick = editor.find_event_node("ReceiveTick")
    tick_pos = tick.get_node_pos() if tick else unreal.Vector2D(0, 0)
    editor.add_comment_node(
        MARKER,
        unreal.Vector2D(tick_pos.x + 120, tick_pos.y + 1200),
        unreal.Vector2D(1300, 420),
    )


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
    wire_freeaim_joystick(editor, bp)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)
    log("Done — left joystick injects MouseX/Y; ADS on touch begin/end in left zone")


main()
