"""Mobile touch zones v5 — match Unity ARTouchInputBridge zones and semantics.

Bottom strip (~14% of screen height):
  Left   0–35%  = ADS (hold)
  Center 35–65% = Reload (tap)
  Right  65–100% = Shoot (tap only; BeginFire on press edge, StopFire on release)

Does NOT pulse IA_Shoot / IfThenElse_50 every tick (that caused full-auto).
"""

import unreal
from pathlib import Path

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_mobile_touch_zones.log")
MARKER = "Mobile Touch Zones v5"
WAS_PRESSED_VAR = "PressedAgain"
AIM_STATE_VAR = "IsAim"

RELOAD_FN = "K2Node_CallFunction_285"
AIM_ON_FN = "K2Node_CallFunction_56"
AIM_OFF_FN = "K2Node_CallFunction_379"
BEGIN_FIRE_FN = "K2Node_CallFunction_86"
STOP_FIRE_FN = "K2Node_CallFunction_61"

# Unity ARTouchInputBridge defaults (commit 4d80a389)
BOTTOM_STRIP_FRAC = 0.14
ADS_ZONE_RIGHT = 0.35
RELOAD_ZONE_LEFT = 0.35
RELOAD_ZONE_RIGHT = 0.65
SHOOT_ZONE_LEFT = 0.65


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[fix_mobile_touch] {msg}")


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


def already_wired(editor) -> bool:
    for node in editor.list_all_nodes():
        if node.get_class().get_name() != "K2Node_Comment":
            continue
        try:
            comment = str(node.get_editor_property("node_comment"))
            if MARKER in comment or "Mobile Touch Zones v4" in comment:
                return True
        except Exception:
            pass
    return False


def find_node(editor, node_name: str):
    for node in editor.list_all_nodes():
        if node.get_name() == node_name:
            return node
    return None


def title(node) -> str:
    return str(node.get_node_title()).replace("\n", " | ")


def find_by_title(editor, exact_title: str, class_name=None):
    for node in editor.list_all_nodes():
        if title(node) != exact_title:
            continue
        if class_name and node.get_class().get_name() != class_name:
            continue
        return node
    return None


def resolve_hooks(editor):
    reload_fn = find_node(editor, RELOAD_FN) or find_by_title(editor, "Reload", "K2Node_CallFunction")
    aim_on_fn = find_node(editor, AIM_ON_FN) or find_by_title(editor, "AIMOn", "K2Node_CallFunction")
    aim_off_fn = find_node(editor, AIM_OFF_FN) or find_by_title(editor, "AIMOff", "K2Node_CallFunction")
    begin_fire = find_node(editor, BEGIN_FIRE_FN) or find_by_title(editor, "BeginFire", "K2Node_CallFunction")
    stop_fire = find_node(editor, STOP_FIRE_FN) or find_by_title(editor, "StopFire", "K2Node_CallFunction")
    return reload_fn, aim_on_fn, aim_off_fn, begin_fire, stop_fire


def multiply_frac(editor, size_pin, frac: float):
    mult = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble")
    pin_value(mult.find_input_pin("B"), f"{frac:.6f}")
    connect_data(size_pin, mult.find_input_pin("A"))
    return mult.find_output_pin("ReturnValue")


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


def compare_loc_frac(editor, loc_pin, size_pin, frac: float, op: str):
    return compare(editor, loc_pin, multiply_frac(editor, size_pin, frac), op)


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


def wire_mobile_touch(bp) -> None:
    event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)
    if already_wired(editor):
        log("Mobile touch v5 already wired")
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

    # UE viewport: origin top-left, Y grows downward → bottom strip is high Y values.
    strip_top_y = 1.0 - BOTTOM_STRIP_FRAC
    in_strip = compare_loc_frac(editor, loc_y, size_y, strip_top_y, "ge")
    in_left = compare_loc_frac(editor, loc_x, size_x, ADS_ZONE_RIGHT, "lt")
    in_center_low = compare_loc_frac(editor, loc_x, size_x, RELOAD_ZONE_LEFT, "ge")
    in_center_high = compare_loc_frac(editor, loc_x, size_x, RELOAD_ZONE_RIGHT, "le")
    in_center_x = bool_and(editor, in_center_low, in_center_high)
    in_right = compare_loc_frac(editor, loc_x, size_x, SHOOT_ZONE_LEFT, "gt")

    bottom_left = bool_and(editor, in_strip, in_left)
    bottom_center = bool_and(editor, in_strip, in_center_x)
    bottom_right = bool_and(editor, in_strip, in_right)

    was_pressed = var_output_pin(get_was, WAS_PRESSED_VAR)
    not_was = bool_not(editor, was_pressed)
    touch_rising = bool_and(editor, pressed, not_was)
    not_pressed = bool_not(editor, pressed)
    touch_falling = bool_and(editor, not_pressed, was_pressed)

    shoot_tap = bool_and(editor, bottom_right, touch_rising)
    reload_tap = bool_and(editor, bottom_center, touch_rising)
    shoot_release = bool_and(editor, bottom_right, touch_falling)

    left_held = bool_and(editor, bottom_left, pressed)
    not_aim = bool_not(editor, var_output_pin(get_aim, AIM_STATE_VAR))
    aim_start_cond = bool_and(editor, left_held, not_aim)

    not_in_left = bool_not(editor, bottom_left)
    release_or_leave = bool_or(editor, not_pressed, not_in_left)
    aim_stop_cond = bool_and(editor, var_output_pin(get_aim, AIM_STATE_VAR), release_or_leave)

    branch_shoot = editor.add_branch_node()
    branch_stop = editor.add_branch_node()
    branch_reload = editor.add_branch_node()
    branch_aim_start = editor.add_branch_node()
    branch_aim_stop = editor.add_branch_node()
    connect_data(shoot_tap, branch_shoot.find_input_pin("Condition"))
    connect_data(shoot_release, branch_stop.find_input_pin("Condition"))
    connect_data(reload_tap, branch_reload.find_input_pin("Condition"))
    connect_data(aim_start_cond, branch_aim_start.find_input_pin("Condition"))
    connect_data(aim_stop_cond, branch_aim_stop.find_input_pin("Condition"))

    shoot_exec = begin_fire.find_execute_pin()
    stop_exec = stop_fire.find_execute_pin()
    reload_exec = reload_fn.find_execute_pin()
    aim_on_exec = aim_on_fn.find_execute_pin()
    aim_off_exec = aim_off_fn.find_execute_pin()

    tick_then = tick.find_then_pin()
    tick_links = unreal.BlueprintGraphPinLibrary.list_connected_pins(tick_then)
    seq_tick = editor.create_node_from_name(
        "Utilities|FlowControl|Sequence",
        unreal.Vector2D(tick_pos.x + 160, tick_pos.y),
        [],
    )
    if not seq_tick:
        raise RuntimeError("Could not create tick Sequence node")
    unreal.BlueprintGraphPinLibrary.break_pin_links(tick_then)
    connect_exec(tick_then, seq_tick.find_execute_pin())
    if tick_links:
        connect_exec(seq_tick.find_output_pin("then_0"), tick_links[0])
    connect_exec(seq_tick.find_output_pin("then_1"), branch_shoot.find_execute_pin())

    wire_branch(branch_shoot, shoot_exec, branch_stop.find_execute_pin())
    wire_branch(branch_stop, stop_exec, branch_reload.find_execute_pin())
    wire_branch(branch_reload, reload_exec, branch_aim_start.find_execute_pin())
    wire_branch(branch_aim_start, aim_on_exec, branch_aim_stop.find_execute_pin())
    wire_branch(branch_aim_stop, aim_off_exec, set_was.find_execute_pin())
    connect_data(pressed, var_input_pin(set_was, WAS_PRESSED_VAR))

    editor.add_comment_node(
        MARKER,
        unreal.Vector2D(tick_pos.x + 120, tick_pos.y + 760),
        unreal.Vector2D(1900, 1100),
    )
    log("Wired mobile touch zones v5 (Unity ARTouchInputBridge parity)")


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
