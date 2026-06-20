"""Mobile touch zones: bottom-left ADS hold, bottom-right shoot tap, bottom-center reload tap."""

import unreal
from pathlib import Path

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_mobile_touch_zones.log")
MARKER = "Mobile Touch Zones"
TOUCH_WAS_VAR = "PressedAgain"
AIM_STATE_VAR = "IsAim"


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


def exec_in_pin(node):
    pin = node.find_execute_pin()
    if pin:
        return pin
    return node.find_input_pin("execute")


def exec_out_pin(node):
    pin = node.find_then_pin()
    if pin:
        return pin
    return node.find_output_pin("then")


def node_title(node) -> str:
    try:
        return str(node.get_node_title()).replace("\n", " | ")
    except Exception:
        return node.get_name()


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
        if candidate.get_name() in ("self", "execute"):
            continue
        return candidate
    raise RuntimeError(f"Missing input pin on {var_name}")


def mobile_touch_already_wired(editor) -> bool:
    for node in editor.list_all_nodes():
        if node.get_class().get_name() != "K2Node_Comment":
            continue
        try:
            if MARKER in str(node.get_editor_property("node_comment")):
                return True
        except Exception:
            pass
    for node in editor.list_all_nodes():
        if node.get_class().get_name() != "K2Node_CallFunction":
            continue
        try:
            title = str(node.get_node_title()).replace("\n", " | ")
        except Exception:
            continue
        if "Get Input Touch State" in title or "GetInputTouchState" in title:
            return True
    return False


def find_ei_node(editor, token: str):
    for node in editor.list_all_nodes():
        if node.get_class().get_name() != "K2Node_EnhancedInputAction":
            continue
        if token in node_title(node):
            return node
    return None


def insert_sequence_on_exec(source_exec_pin, target_exec_pin, editor, pos: unreal.IntPoint):
    seq = editor.create_node_from_name(
        "Utilities|FlowControl|Sequence",
        unreal.Vector2D(pos.x, pos.y),
        [],
    )
    if not seq:
        raise RuntimeError("Could not create Sequence node")
    unreal.BlueprintGraphPinLibrary.break_pin_links(source_exec_pin)
    connect_exec(source_exec_pin, seq.find_execute_pin())
    connect_exec(seq.find_output_pin("then_0"), target_exec_pin)
    return target_exec_pin


def add_compare_mult(editor, loc_pin, size_pin, threshold: float, op: str):
    mult = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble")
    pin_value(mult.find_input_pin("B"), f"{threshold:.6f}")
    connect_data(size_pin, mult.find_input_pin("A"))
    if op == "gt":
        cmp_node = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.Greater_DoubleDouble")
        connect_data(loc_pin, cmp_node.find_input_pin("A"))
        connect_data(mult.find_output_pin("ReturnValue"), cmp_node.find_input_pin("B"))
    elif op == "lt":
        cmp_node = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.Less_DoubleDouble")
        connect_data(loc_pin, cmp_node.find_input_pin("A"))
        connect_data(mult.find_output_pin("ReturnValue"), cmp_node.find_input_pin("B"))
    else:
        raise ValueError(op)
    return cmp_node.find_output_pin("ReturnValue")


def wire_mobile_touch(bp) -> None:
    event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)
    if mobile_touch_already_wired(editor):
        log("Mobile touch already wired")
        return

    hooks = {}
    anchor = unreal.IntPoint(-4200, 5400)
    mapping = (
        ("reload", "IA_Reload", "Triggered"),
        ("shoot", "IA_Shoot", "Started"),
        ("aim_start", "IA_Aim", "Started"),
        ("aim_stop", "IA_Aim", "Completed"),
    )
    y = anchor.y
    for key, token, pin_name in mapping:
        ei = find_ei_node(editor, token)
        if not ei:
            continue
        out = ei.find_output_pin(pin_name)
        if not out:
            continue
        links = unreal.BlueprintGraphPinLibrary.list_connected_pins(out)
        if not links:
            continue
        hooks[key] = insert_sequence_on_exec(out, links[0], editor, unreal.IntPoint(anchor.x, y))
        y += 180
        log(f"Inserted mobile hook on {token}.{pin_name}")

    tick = editor.find_event_node("ReceiveTick")
    if not tick:
        raise RuntimeError("ReceiveTick missing")
    tick_pos = tick.get_node_pos()

    get_pc = editor.add_call_function_node("/Script/Engine.GameplayStatics.GetPlayerController")
    get_touch = editor.add_call_function_node("/Script/Engine.PlayerController.GetInputTouchState")
    get_viewport = editor.add_call_function_node("/Script/UMG.WidgetLayoutLibrary.GetViewportSize")
    break_vec = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.BreakVector2D")
    get_was = editor.add_get_member_variable_node(TOUCH_WAS_VAR)
    set_was = editor.add_set_member_variable_node(TOUCH_WAS_VAR)
    get_aim = editor.add_get_member_variable_node(AIM_STATE_VAR)
    if not get_was or not set_was or not get_aim:
        raise RuntimeError(f"Missing BP vars {TOUCH_WAS_VAR}/{AIM_STATE_VAR}")

    pin_value(get_pc.find_input_pin("PlayerIndex"), "0")
    pin_value(get_pc.find_input_pin("WorldContextObject"), "self")
    pin_value(get_viewport.find_input_pin("WorldContextObject"), "self")
    pin_value(get_touch.find_input_pin("FingerIndex"), "0")

    loc_x = get_touch.find_output_pin("LocationX")
    loc_y = get_touch.find_output_pin("LocationY")
    pressed = get_touch.find_output_pin("bIsCurrentlyPressed")
    size_x = break_vec.find_output_pin("X")
    size_y = break_vec.find_output_pin("Y")

    in_bottom = add_compare_mult(editor, loc_y, size_y, 0.55, "gt")
    in_left = add_compare_mult(editor, loc_x, size_x, 0.35, "lt")
    in_right = add_compare_mult(editor, loc_x, size_x, 0.65, "gt")
    not_left = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.Not_PreBool")
    not_right = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.Not_PreBool")
    connect_data(in_left, not_left.find_input_pin("A"))
    connect_data(in_right, not_right.find_input_pin("A"))
    in_center = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.BooleanAND")
    connect_data(not_left.find_output_pin("ReturnValue"), in_center.find_input_pin("A"))
    connect_data(not_right.find_output_pin("ReturnValue"), in_center.find_input_pin("B"))

    not_was = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.Not_PreBool")
    connect_data(var_output_pin(get_was, TOUCH_WAS_VAR), not_was.find_input_pin("A"))
    rising = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.BooleanAND")
    connect_data(pressed, rising.find_input_pin("A"))
    connect_data(not_was.find_output_pin("ReturnValue"), rising.find_input_pin("B"))

    not_aim = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.Not_PreBool")
    connect_data(var_output_pin(get_aim, AIM_STATE_VAR), not_aim.find_input_pin("A"))
    aim_start_gate = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.BooleanAND")
    connect_data(pressed, aim_start_gate.find_input_pin("A"))
    connect_data(not_aim.find_output_pin("ReturnValue"), aim_start_gate.find_input_pin("B"))

    bottom_and_left = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.BooleanAND")
    connect_data(in_bottom, bottom_and_left.find_input_pin("A"))
    connect_data(in_left, bottom_and_left.find_input_pin("B"))
    bottom_and_right = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.BooleanAND")
    connect_data(in_bottom, bottom_and_right.find_input_pin("A"))
    connect_data(in_right, bottom_and_right.find_input_pin("B"))
    bottom_and_center = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.BooleanAND")
    connect_data(in_bottom, bottom_and_center.find_input_pin("A"))
    connect_data(in_center.find_output_pin("ReturnValue"), bottom_and_center.find_input_pin("B"))

    shoot_gate = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.BooleanAND")
    connect_data(bottom_and_right.find_output_pin("ReturnValue"), shoot_gate.find_input_pin("A"))
    connect_data(rising.find_output_pin("ReturnValue"), shoot_gate.find_input_pin("B"))
    reload_gate = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.BooleanAND")
    connect_data(bottom_and_center.find_output_pin("ReturnValue"), reload_gate.find_input_pin("A"))
    connect_data(rising.find_output_pin("ReturnValue"), reload_gate.find_input_pin("B"))
    aim_start_cond = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.BooleanAND")
    connect_data(bottom_and_left.find_output_pin("ReturnValue"), aim_start_cond.find_input_pin("A"))
    connect_data(aim_start_gate.find_output_pin("ReturnValue"), aim_start_cond.find_input_pin("B"))

    not_pressed = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.Not_PreBool")
    connect_data(pressed, not_pressed.find_input_pin("A"))
    not_in_left = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.Not_PreBool")
    connect_data(bottom_and_left.find_output_pin("ReturnValue"), not_in_left.find_input_pin("A"))
    leave_zone = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.BooleanAND")
    connect_data(not_in_left.find_output_pin("ReturnValue"), leave_zone.find_input_pin("A"))
    connect_data(pressed, leave_zone.find_input_pin("B"))
    release_aim = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.BooleanAND")
    connect_data(not_pressed.find_output_pin("ReturnValue"), release_aim.find_input_pin("A"))
    connect_data(var_output_pin(get_aim, AIM_STATE_VAR), release_aim.find_input_pin("B"))
    stop_aim = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.BooleanOR")
    connect_data(leave_zone.find_output_pin("ReturnValue"), stop_aim.find_input_pin("A"))
    connect_data(release_aim.find_output_pin("ReturnValue"), stop_aim.find_input_pin("B"))
    aim_stop_cond = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.BooleanAND")
    connect_data(stop_aim.find_output_pin("ReturnValue"), aim_stop_cond.find_input_pin("A"))
    connect_data(var_output_pin(get_aim, AIM_STATE_VAR), aim_stop_cond.find_input_pin("B"))

    branch_shoot = editor.add_branch_node()
    branch_reload = editor.add_branch_node()
    branch_aim_start = editor.add_branch_node()
    branch_aim_stop = editor.add_branch_node()

    connect_data(shoot_gate.find_output_pin("ReturnValue"), branch_shoot.find_input_pin("Condition"))
    connect_data(reload_gate.find_output_pin("ReturnValue"), branch_reload.find_input_pin("Condition"))
    connect_data(aim_start_cond.find_output_pin("ReturnValue"), branch_aim_start.find_input_pin("Condition"))
    connect_data(aim_stop_cond.find_output_pin("ReturnValue"), branch_aim_stop.find_input_pin("Condition"))

    tick_then = tick.find_then_pin()
    tick_links = unreal.BlueprintGraphPinLibrary.list_connected_pins(tick_then)
    if tick_links:
        seq_tick = editor.create_node_from_name(
            "Utilities|FlowControl|Sequence",
            unreal.Vector2D(tick_pos.x + 160, tick_pos.y),
            [],
        )
        if not seq_tick:
            raise RuntimeError("Could not create tick Sequence node")
        unreal.BlueprintGraphPinLibrary.break_pin_links(tick_then)
        connect_exec(tick_then, seq_tick.find_execute_pin())
        connect_exec(seq_tick.find_output_pin("then_0"), tick_links[0])
        connect_exec(seq_tick.find_output_pin("then_1"), branch_shoot.find_execute_pin())
    else:
        connect_exec(tick_then, branch_shoot.find_execute_pin())

    connect_data(get_pc.find_output_pin("ReturnValue"), get_touch.find_input_pin("self"))
    connect_data(get_viewport.find_output_pin("ReturnValue"), break_vec.find_input_pin("InVec"))

    if hooks.get("shoot"):
        connect_exec(branch_shoot.find_then_pin(), hooks["shoot"])
    connect_exec(branch_shoot.find_then_pin(), branch_reload.find_execute_pin())
    if hooks.get("reload"):
        connect_exec(branch_reload.find_then_pin(), hooks["reload"])
    connect_exec(branch_reload.find_then_pin(), branch_aim_start.find_execute_pin())
    if hooks.get("aim_start"):
        connect_exec(branch_aim_start.find_then_pin(), hooks["aim_start"])
    connect_exec(branch_aim_start.find_then_pin(), branch_aim_stop.find_execute_pin())
    if hooks.get("aim_stop"):
        connect_exec(branch_aim_stop.find_then_pin(), hooks["aim_stop"])
    connect_exec(branch_aim_stop.find_then_pin(), set_was.find_execute_pin())
    connect_data(pressed, var_input_pin(set_was, TOUCH_WAS_VAR))

    editor.add_comment_node(
        MARKER,
        unreal.Vector2D(tick_pos.x + 120, tick_pos.y + 640),
        unreal.Vector2D(1700, 900),
    )
    log("Wired mobile touch zones")


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
