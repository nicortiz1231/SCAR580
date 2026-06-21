"""Mobile touch v6: zone-only combat matching mockup (bottom half, equal thirds).

Left hold = ADS, center tap = reload, right tap = shoot (BeginFire/StopFire).
Fully disconnects IA_Shoot from LMB/touch input path.
"""

import unreal
from pathlib import Path

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_mobile_touch_v6.log")
MARKER = "Mobile Touch Zones v6"
WAS_PRESSED_VAR = "PressedAgain"
AIM_STATE_VAR = "IsAim"

RELOAD_FN = "K2Node_CallFunction_285"
AIM_ON_FN = "K2Node_CallFunction_56"
AIM_OFF_FN = "K2Node_CallFunction_379"
BEGIN_FIRE_FN = "K2Node_CallFunction_86"
STOP_FIRE_FN = "K2Node_CallFunction_61"
IA_SHOOT_NODE = "K2Node_EnhancedInputAction_24"
SHOOT_BRANCH = "K2Node_IfThenElse_50"

# Mockup: large bottom control area, equal left/center/right thirds
BOTTOM_FRAC = 0.50
LEFT_X_FRAC = 0.333333
RIGHT_X_FRAC = 0.666667

TOUCH_MARKERS = (
    "Mobile Touch Zones v",
    "Mobile Suppress LMB Shoot",
)


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[touch_v6] {msg}")


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


def find_node(editor, name: str):
    for node in editor.list_all_nodes():
        if node.get_name() == name:
            return node
    return None


def find_by_title(editor, exact_title: str, class_name=None):
    for node in editor.list_all_nodes():
        if title(node) != exact_title:
            continue
        if class_name and node.get_class().get_name() != class_name:
            continue
        return node
    return None


def divide(editor, a_pin, b_pin):
    node = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.Divide_DoubleDouble")
    connect_data(a_pin, node.find_input_pin("A"))
    connect_data(b_pin, node.find_input_pin("B"))
    return node.find_output_pin("ReturnValue")


def compare(editor, a_pin, b_pin, op: str):
    ops = {
        "lt": "/Script/Engine.KismetMathLibrary.Less_DoubleDouble",
        "le": "/Script/Engine.KismetMathLibrary.LessEqual_DoubleDouble",
        "gt": "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble",
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


def bool_not(editor, a_pin):
    node = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.Not_PreBool")
    connect_data(a_pin, node.find_input_pin("A"))
    return node.find_output_pin("ReturnValue")


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


def is_touch_marker_comment(node) -> bool:
    if node.get_class().get_name() != "K2Node_Comment":
        return False
    try:
        text = str(node.get_editor_property("node_comment"))
    except Exception:
        return False
    return any(m in text for m in TOUCH_MARKERS)


def cleanup_old_touch(editor) -> None:
    stop = {
        SHOOT_BRANCH,
        "K2Node_IfThenElse_11",
        RELOAD_FN,
        AIM_ON_FN,
        AIM_OFF_FN,
        "K2Node_CallFunction_153",
        IA_SHOOT_NODE,
    }
    remove = set()
    for node in editor.list_all_nodes():
        if is_touch_marker_comment(node):
            remove.add(node)
        if "GetInputTouchState" in title(node):
            remove.add(node)

    tick = editor.find_event_node("ReceiveTick")
    recoil = None
    if tick:
        then = tick.find_then_pin()
        seq = None
        for linked in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
            n = unreal.BlueprintGraphPinLibrary.get_owning_node(linked)
            if n and "Sequence" in title(n):
                seq = n
                pin0 = n.find_output_pin("then_0")
                if pin0:
                    for linked2 in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin0):
                        n2 = unreal.BlueprintGraphPinLibrary.get_owning_node(linked2)
                        if n2 and "Recoil" in title(n2):
                            recoil = n2
        if seq:
            remove.add(seq)
            stack = []
            pin1 = seq.find_output_pin("then_1")
            if pin1:
                for linked2 in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin1):
                    n = unreal.BlueprintGraphPinLibrary.get_owning_node(linked2)
                    if n and n.get_name() not in stop:
                        stack.append(n)
            while stack:
                n = stack.pop()
                if n in remove or n.get_name() in stop:
                    continue
                remove.add(n)
                cls = n.get_class().get_name()
                pins = []
                then = n.find_then_pin()
                if then:
                    pins.append(then)
                if cls == "K2Node_IfThenElse":
                    else_pin = n.find_else_pin()
                    if else_pin:
                        pins.append(else_pin)
                for pin in pins:
                    for linked2 in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                        n2 = unreal.BlueprintGraphPinLibrary.get_owning_node(linked2)
                        if n2 and n2.get_name() not in stop and n2 not in remove:
                            stack.append(n2)
        unreal.BlueprintGraphPinLibrary.break_pin_links(then)
        if recoil:
            then.try_create_connection(recoil.find_execute_pin())

    if remove:
        editor.remove_nodes(list(remove))
        log(f"Cleaned {len(remove)} old touch/suppress nodes")


def disconnect_ia_shoot(editor) -> None:
    ia = find_node(editor, IA_SHOOT_NODE)
    if not ia:
        for node in editor.list_all_nodes():
            if node.get_class().get_name() == "K2Node_EnhancedInputAction" and "IA_Shoot" in title(node):
                ia = node
                break
    if not ia:
        raise RuntimeError("IA_Shoot node missing")

    broken = 0
    for pin_name in ("Started", "Triggered", "Ongoing"):
        pin = ia.find_output_pin(pin_name)
        if not pin:
            continue
        links = unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)
        if links:
            unreal.BlueprintGraphPinLibrary.break_pin_links(pin)
            broken += len(links)
            log(f"Broke IA_Shoot.{pin_name} exec ({len(links)} link(s))")
    if broken == 0:
        log("IA_Shoot exec outputs already disconnected")


def already_wired(editor) -> bool:
    for node in editor.list_all_nodes():
        if is_touch_marker_comment(node):
            try:
                if MARKER in str(node.get_editor_property("node_comment")):
                    return True
            except Exception:
                pass
    return False


def resolve_hooks(editor):
    reload_fn = find_node(editor, RELOAD_FN) or find_by_title(editor, "Reload", "K2Node_CallFunction")
    aim_on_fn = find_node(editor, AIM_ON_FN) or find_by_title(editor, "AIMOn", "K2Node_CallFunction")
    aim_off_fn = find_node(editor, AIM_OFF_FN) or find_by_title(editor, "AIMOff", "K2Node_CallFunction")
    begin_fire = find_node(editor, BEGIN_FIRE_FN) or find_by_title(editor, "BeginFire", "K2Node_CallFunction")
    stop_fire = find_node(editor, STOP_FIRE_FN) or find_by_title(editor, "StopFire", "K2Node_CallFunction")
    return reload_fn, aim_on_fn, aim_off_fn, begin_fire, stop_fire


def wire_mobile_touch(bp) -> None:
    event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)

    cleanup_old_touch(editor)
    disconnect_ia_shoot(editor)

    if already_wired(editor):
        log("v6 already wired")
        return

    reload_fn, aim_on_fn, aim_off_fn, begin_fire, stop_fire = resolve_hooks(editor)
    if not all((reload_fn, aim_on_fn, aim_off_fn, begin_fire, stop_fire)):
        raise RuntimeError("Missing combat hook nodes")

    tick = editor.find_event_node("ReceiveTick")
    if not tick:
        raise RuntimeError("ReceiveTick missing")
    tick_pos = tick.get_node_pos()

    get_pc = editor.add_call_function_node("/Script/Engine.GameplayStatics.GetPlayerController")
    get_touch = editor.add_call_function_node("/Script/Engine.PlayerController.GetInputTouchState")
    get_viewport = editor.add_call_function_node("/Script/UMG.WidgetLayoutLibrary.GetViewportSize")
    break_vec = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.BreakVector2D")
    get_was = editor.add_get_member_variable_node(WAS_PRESSED_VAR)
    set_was = editor.add_set_member_variable_node(WAS_PRESSED_VAR)
    get_aim = editor.add_get_member_variable_node(AIM_STATE_VAR)
    if not all((get_pc, get_touch, get_viewport, break_vec, get_was, set_was, get_aim)):
        raise RuntimeError(f"Missing helper nodes or vars ({WAS_PRESSED_VAR}/{AIM_STATE_VAR})")

    pin_value(get_pc.find_input_pin("PlayerIndex"), "0")
    pin_value(get_pc.find_input_pin("WorldContextObject"), "self")
    pin_value(get_viewport.find_input_pin("WorldContextObject"), "self")
    pin_value(get_touch.find_input_pin("FingerIndex"), "0")

    loc_x = get_touch.find_output_pin("LocationX")
    loc_y = get_touch.find_output_pin("LocationY")
    pressed = get_touch.find_output_pin("bIsCurrentlyPressed")
    size_x = break_vec.find_output_pin("X")
    size_y = break_vec.find_output_pin("Y")

    connect_data(get_pc.find_output_pin("ReturnValue"), get_touch.find_input_pin("self"))
    connect_data(get_viewport.find_output_pin("ReturnValue"), break_vec.find_input_pin("InVec"))

    norm_x = divide(editor, loc_x, size_x)
    norm_y = divide(editor, loc_y, size_y)

    strip_top = 1.0 - BOTTOM_FRAC
    in_strip = compare_const(editor, norm_y, strip_top, "ge")
    in_left = compare_const(editor, norm_x, LEFT_X_FRAC, "lt")
    in_center_lo = compare_const(editor, norm_x, LEFT_X_FRAC, "ge")
    in_center_hi = compare_const(editor, norm_x, RIGHT_X_FRAC, "le")
    in_center = bool_and(editor, in_center_lo, in_center_hi)
    in_right = compare_const(editor, norm_x, RIGHT_X_FRAC, "gt")

    bottom_left = bool_and(editor, in_strip, in_left)
    bottom_center = bool_and(editor, in_strip, in_center)
    bottom_right = bool_and(editor, in_strip, in_right)

    was_pressed = var_output_pin(get_was, WAS_PRESSED_VAR)
    touch_rising = bool_and(editor, pressed, bool_not(editor, was_pressed))
    touch_falling = bool_and(editor, bool_not(editor, pressed), was_pressed)

    shoot_tap = bool_and(editor, bottom_right, touch_rising)
    reload_tap = bool_and(editor, bottom_center, touch_rising)
    shoot_release = bool_and(editor, bottom_right, touch_falling)

    left_held = bool_and(editor, bottom_left, pressed)
    aim_start = bool_and(editor, left_held, bool_not(editor, var_output_pin(get_aim, AIM_STATE_VAR)))
    aim_stop = bool_and(
        editor,
        var_output_pin(get_aim, AIM_STATE_VAR),
        bool_or(editor, bool_not(editor, pressed), bool_not(editor, bottom_left)),
    )

    branch_shoot = editor.add_branch_node()
    branch_stop = editor.add_branch_node()
    branch_reload = editor.add_branch_node()
    branch_aim_on = editor.add_branch_node()
    branch_aim_off = editor.add_branch_node()
    connect_data(shoot_tap, branch_shoot.find_input_pin("Condition"))
    connect_data(shoot_release, branch_stop.find_input_pin("Condition"))
    connect_data(reload_tap, branch_reload.find_input_pin("Condition"))
    connect_data(aim_start, branch_aim_on.find_input_pin("Condition"))
    connect_data(aim_stop, branch_aim_off.find_input_pin("Condition"))

    tick_then = tick.find_then_pin()
    tick_links = unreal.BlueprintGraphPinLibrary.list_connected_pins(tick_then)
    seq_tick = editor.create_node_from_name(
        "Utilities|FlowControl|Sequence",
        unreal.Vector2D(tick_pos.x + 160, tick_pos.y),
        [],
    )
    if not seq_tick:
        raise RuntimeError("Could not create tick Sequence")
    unreal.BlueprintGraphPinLibrary.break_pin_links(tick_then)
    connect_exec(tick_then, seq_tick.find_execute_pin())
    if tick_links:
        connect_exec(seq_tick.find_output_pin("then_0"), tick_links[0])
    connect_exec(seq_tick.find_output_pin("then_1"), branch_shoot.find_execute_pin())

    wire_branch(branch_shoot, begin_fire.find_execute_pin(), branch_stop.find_execute_pin())
    wire_branch(branch_stop, stop_fire.find_execute_pin(), branch_reload.find_execute_pin())
    wire_branch(branch_reload, reload_fn.find_execute_pin(), branch_aim_on.find_execute_pin())
    wire_branch(branch_aim_on, aim_on_fn.find_execute_pin(), branch_aim_off.find_execute_pin())
    wire_branch(branch_aim_off, aim_off_fn.find_execute_pin(), set_was.find_execute_pin())
    connect_data(pressed, var_input_pin(set_was, WAS_PRESSED_VAR))

    editor.add_comment_node(
        MARKER,
        unreal.Vector2D(tick_pos.x + 120, tick_pos.y + 760),
        unreal.Vector2D(1900, 1100),
    )
    log("Wired v6: bottom-half thirds, normalized coords, IA_Shoot disconnected")


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()
    bp = unreal.load_asset(BP_ASSET)
    if not bp:
        raise RuntimeError(f"Missing {BP_ASSET}")
    wire_mobile_touch(bp)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)
    log("Done")


main()
