"""Left button hold + drag -> FreeAimComponent (Bodycam-style arm aim).

ADS stays on TouchInterface LeftShift button (unchanged). Touch movement delta in the
left bottom zone is added to AC_FreeAim mouse inputs while held.
"""
import unreal
from pathlib import Path

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/wire_mobile_left_ads_hold.log")
MARKER = "Mobile Left FreeAim Drag v4"
RECOIL_NODE = "K2Node_CallFunction_153"
MARKER_EXEC = "Mobile Touch Prev Exec"
OLD_MARKERS = (
    "Mobile Left FreeAim Drag",
    "Mobile Left FreeAim Drag v2",
    "Mobile Left FreeAim Drag v3",
    "Mobile Left FreeAim Drag v4",
    "Mobile Left Zone FreeAim",
    "Mobile Left FreeAim Touch",
    "Mobile Left ADS Hold",
    "Mobile Left ADS Touch Events",
    MARKER_EXEC,
)

MOUSE_X_NODE = "K2Node_GetInputAxisKeyValue_0"
MOUSE_Y_NODE = "K2Node_GetInputAxisKeyValue_1"
FREEAIM_NODE = "K2Node_CallFunction_23"
FREEAIM_TRANSFORM_SET = "K2Node_VariableSet_25"

PREV_X_VAR = "MobileTouchPrevX"
PREV_Y_VAR = "MobileTouchPrevY"
HAS_PREV_VAR = "MobileTouchHasPrev"

# Match create_mobile_touch_interface.py
LEFT_X = 0.17
VISUAL_SIZE = 0.22
BOTTOM_FRAC = 0.50
LEFT_X_FRAC = 0.333333
TOUCH_SENS = 22.0

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
    unreal.log(f"[freeaim_drag] {msg}")


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


def subtract(editor, a_pin, b_pin):
    node = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.Subtract_DoubleDouble")
    connect_data(a_pin, node.find_input_pin("A"))
    connect_data(b_pin, node.find_input_pin("B"))
    return node.find_output_pin("ReturnValue")


def multiply_const(editor, a_pin, value: float):
    node = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble")
    pin_value(node.find_input_pin("B"), f"{value:.8f}")
    connect_data(a_pin, node.find_input_pin("A"))
    return node.find_output_pin("ReturnValue")


def multiply(editor, a_pin, b_pin):
    node = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble")
    connect_data(a_pin, node.find_input_pin("A"))
    connect_data(b_pin, node.find_input_pin("B"))
    return node.find_output_pin("ReturnValue")


def add(editor, a_pin, b_pin):
    node = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.Add_DoubleDouble")
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


def bool_or(editor, a_pin, b_pin):
    node = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.BooleanOR")
    connect_data(a_pin, node.find_input_pin("A"))
    connect_data(b_pin, node.find_input_pin("B"))
    return node.find_output_pin("ReturnValue")


def bool_and(editor, a_pin, b_pin):
    node = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.BooleanAND")
    connect_data(a_pin, node.find_input_pin("A"))
    connect_data(b_pin, node.find_input_pin("B"))
    return node.find_output_pin("ReturnValue")


def bool_to_float(editor, bool_pin):
    node = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.Conv_BoolToDouble")
    connect_data(bool_pin, node.find_input_pin("InBool"))
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
    markers = OLD_MARKERS
    remove = set()
    for node in editor.list_all_nodes():
        if is_marker(node, markers):
            remove.add(node)
        if title(node) in ("Event BeginInputTouch", "Event EndInputTouch"):
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
            for linked in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                n2 = unreal.BlueprintGraphPinLibrary.get_owning_node(linked)
                if n2 and n2.get_name() not in PROTECT and n2 not in remove:
                    stack.append(n2)

    if remove:
        editor.remove_nodes(list(remove))
        log(f"Removed {len(remove)} old mobile-left nodes")


def cleanup_freeaim_touch_feed(editor, freeaim, mouse_x, mouse_y) -> None:
    protected = set(PROTECT) | {mouse_x.get_name(), mouse_y.get_name()}
    start_pins = []
    for pin_name in ("HorizontalMouse", "VerticalMouse"):
        pin = freeaim.find_input_pin(pin_name)
        if not pin:
            continue
        start_pins.extend(unreal.BlueprintGraphPinLibrary.list_connected_pins(pin))

    remove = collect_upstream_data_nodes(start_pins, protected)
    for pin_name in ("HorizontalMouse", "VerticalMouse"):
        pin = freeaim.find_input_pin(pin_name)
        if pin:
            unreal.BlueprintGraphPinLibrary.break_pin_links(pin)
    if remove:
        editor.remove_nodes(list(remove))
        log(f"Removed {len(remove)} old FreeAim touch feed nodes")


def cleanup_touch_prev_exec(editor, freeaim) -> None:
    transform_set = find_node(editor, FREEAIM_TRANSFORM_SET)
    if not transform_set:
        return

    then_links = unreal.BlueprintGraphPinLibrary.list_connected_pins(freeaim.find_then_pin())
    for linked in list(then_links):
        node = unreal.BlueprintGraphPinLibrary.get_owning_node(linked)
        if not node or node.get_name() == transform_set.get_name():
            continue
        unreal.BlueprintGraphPinLibrary.break_pin_links(freeaim.find_then_pin())
        remove = set()
        stack = [node]
        while stack:
            n = stack.pop()
            if n.get_name() in PROTECT:
                continue
            remove.add(n)
            then = n.find_then_pin()
            if not then:
                continue
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
                n2 = unreal.BlueprintGraphPinLibrary.get_owning_node(lp)
                if n2 and n2.get_name() != transform_set.get_name() and n2 not in remove:
                    stack.append(n2)
        if remove:
            editor.remove_nodes(list(remove))
            log(f"Removed {len(remove)} old touch-prev exec nodes")
        connect_exec(freeaim.find_then_pin(), transform_set.find_execute_pin())
        break


def ensure_member_vars(editor, bp) -> None:
    names = set(unreal.BlueprintEditorLibrary.list_member_variable_names(bp))
    float_type = unreal.BlueprintEditorLibrary.get_member_variable_type(bp, "MouseSens")
    bool_type = unreal.BlueprintEditorLibrary.get_member_variable_type(bp, "IsAim")
    for var_name in (PREV_X_VAR, PREV_Y_VAR):
        if var_name not in names:
            editor.add_member_variable(var_name, float_type)
            log(f"Added float member {var_name}")
        else:
            unreal.BlueprintEditorLibrary.change_member_variable_type(bp, var_name, float_type)
    if HAS_PREV_VAR not in names:
        editor.add_member_variable(HAS_PREV_VAR, bool_type)
        log(f"Added bool member {HAS_PREV_VAR}")


def _exec_out_pins(node):
    pins = []
    then_pin = node.find_then_pin()
    if then_pin:
        pins.append(then_pin)
    if node.get_class().get_name() == "K2Node_IfThenElse":
        else_pin = node.find_else_pin()
        if else_pin:
            pins.append(else_pin)
    if node.get_class().get_name() == "K2Node_MultiGate":
        for candidate in unreal.BlueprintEditorLibrary.list_all_pins(node):
            if unreal.BlueprintGraphPinLibrary.get_pin_direction(candidate) != unreal.EdGraphPinDirection.EGPD_OUTPUT:
                continue
            if str(unreal.BlueprintGraphPinLibrary.get_pin_name(candidate)).startswith("then_"):
                pins.append(candidate)
    if node.get_class().get_name() == "K2Node_ExecutionSequence":
        for candidate in unreal.BlueprintEditorLibrary.list_all_pins(node):
            if unreal.BlueprintGraphPinLibrary.get_pin_direction(candidate) != unreal.EdGraphPinDirection.EGPD_OUTPUT:
                continue
            if str(unreal.BlueprintGraphPinLibrary.get_pin_name(candidate)).startswith("then_"):
                pins.append(candidate)
    return pins


def exec_chain_reaches_from_tick(editor, tick, target_name: str, max_depth: int = 48) -> bool:
    """True if any exec path from ReceiveTick reaches the target node name."""
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
    """ReceiveTick must drive Recoil -> CameraShake -> FreeAim every frame."""
    tick = editor.find_event_node("ReceiveTick")
    recoil = find_node(editor, RECOIL_NODE)
    if not tick or not recoil:
        raise RuntimeError("Missing ReceiveTick or Recoil node")

    recoil_exec = recoil.find_input_pin("execute") or recoil.find_execute_pin()
    if exec_chain_reaches_from_tick(editor, tick, RECOIL_NODE):
        log("ReceiveTick already reaches Recoil on exec chain")
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
        connect_exec(seq.find_output_pin("then_0"), recoil_exec)
        connect_exec(seq.find_output_pin("then_1"), existing[0])
        log("Inserted Sequence: ReceiveTick -> Recoil + existing tick branch")
        return

    unreal.BlueprintGraphPinLibrary.break_pin_links(tick_then)
    connect_exec(tick_then, recoil_exec)
    log("Restored ReceiveTick -> Recoil (FreeAim runs every frame)")


def primary_left_touch(editor):
    get_pc = editor.add_call_function_node("/Script/Engine.GameplayStatics.GetPlayerController")
    get_touch0 = editor.add_call_function_node("/Script/Engine.PlayerController.GetInputTouchState")
    get_touch1 = editor.add_call_function_node("/Script/Engine.PlayerController.GetInputTouchState")
    get_viewport = editor.add_call_function_node("/Script/UMG.WidgetLayoutLibrary.GetViewportSize")
    break_vec = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.BreakVector2D")
    get_is_aim = editor.add_get_member_variable_node("IsAim")
    pin_value(get_pc.find_input_pin("PlayerIndex"), "0")
    pin_value(get_pc.find_input_pin("WorldContextObject"), "self")
    pin_value(get_viewport.find_input_pin("WorldContextObject"), "self")
    pin_value(get_touch0.find_input_pin("FingerIndex"), "0")
    pin_value(get_touch1.find_input_pin("FingerIndex"), "1")
    connect_data(get_pc.find_output_pin("ReturnValue"), get_touch0.find_input_pin("self"))
    connect_data(get_pc.find_output_pin("ReturnValue"), get_touch1.find_input_pin("self"))
    connect_data(get_viewport.find_output_pin("ReturnValue"), break_vec.find_input_pin("InVec"))

    pressed0 = get_touch0.find_output_pin("bIsCurrentlyPressed")
    pressed1 = get_touch1.find_output_pin("bIsCurrentlyPressed")
    use_touch1 = bool_and(editor, bool_not(editor, pressed0), pressed1)

    loc_x = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.SelectFloat")
    loc_y = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.SelectFloat")
    connect_data(use_touch1, loc_x.find_input_pin("bPickA"))
    connect_data(use_touch1, loc_y.find_input_pin("bPickA"))
    connect_data(get_touch0.find_output_pin("LocationX"), loc_x.find_input_pin("A"))
    connect_data(get_touch1.find_output_pin("LocationX"), loc_x.find_input_pin("B"))
    connect_data(get_touch0.find_output_pin("LocationY"), loc_y.find_input_pin("A"))
    connect_data(get_touch1.find_output_pin("LocationY"), loc_y.find_input_pin("B"))
    norm_x = divide(editor, loc_x.find_output_pin("ReturnValue"), break_vec.find_output_pin("X"))
    norm_y = divide(editor, loc_y.find_output_pin("ReturnValue"), break_vec.find_output_pin("Y"))

    is_aim = var_output_pin(get_is_aim, "IsAim")
    any_pressed = bool_or(editor, pressed0, pressed1)
    active = bool_and(editor, is_aim, any_pressed)
    return norm_x, norm_y, active


def touch_delta(editor, norm_x, norm_y, active):
    get_prev_x = editor.add_get_member_variable_node(PREV_X_VAR)
    get_prev_y = editor.add_get_member_variable_node(PREV_Y_VAR)
    get_has = editor.add_get_member_variable_node(HAS_PREV_VAR)

    raw_dx = multiply_const(
        editor,
        subtract(editor, norm_x, var_output_pin(get_prev_x, PREV_X_VAR)),
        TOUCH_SENS,
    )
    raw_dy = multiply_const(
        editor,
        subtract(editor, var_output_pin(get_prev_y, PREV_Y_VAR), norm_y),
        TOUCH_SENS,
    )
    scale = multiply(
        editor,
        bool_to_float(editor, active),
        bool_to_float(editor, var_output_pin(get_has, HAS_PREV_VAR)),
    )
    return multiply(editor, raw_dx, scale), multiply(editor, raw_dy, scale)


def wire_touch_prev_exec(editor, freeaim, norm_x, norm_y, active) -> None:
    transform_set = find_node(editor, FREEAIM_TRANSFORM_SET)
    if not transform_set:
        raise RuntimeError(f"Missing {FREEAIM_TRANSFORM_SET}")

    set_prev_x = editor.add_set_member_variable_node(PREV_X_VAR)
    set_prev_y = editor.add_set_member_variable_node(PREV_Y_VAR)
    set_has_true = editor.add_set_member_variable_node(HAS_PREV_VAR)
    set_has_false = editor.add_set_member_variable_node(HAS_PREV_VAR)
    branch = editor.add_branch_node()

    connect_data(active, branch.find_input_pin("Condition"))
    unreal.BlueprintGraphPinLibrary.break_pin_links(freeaim.find_then_pin())
    connect_exec(freeaim.find_then_pin(), branch.find_execute_pin())

    connect_exec(branch.find_then_pin(), set_prev_x.find_execute_pin())
    connect_data(norm_x, var_input_pin(set_prev_x, PREV_X_VAR))
    connect_exec(set_prev_x.find_then_pin(), set_prev_y.find_execute_pin())
    connect_data(norm_y, var_input_pin(set_prev_y, PREV_Y_VAR))
    connect_exec(set_prev_y.find_then_pin(), set_has_true.find_execute_pin())
    pin_value(var_input_pin(set_has_true, HAS_PREV_VAR), "true")
    connect_exec(set_has_true.find_then_pin(), transform_set.find_execute_pin())

    connect_exec(branch.find_else_pin(), set_has_false.find_execute_pin())
    pin_value(var_input_pin(set_has_false, HAS_PREV_VAR), "false")
    connect_exec(set_has_false.find_then_pin(), transform_set.find_execute_pin())

    pos = freeaim.get_node_pos()
    editor.add_comment_node(
        MARKER_EXEC,
        unreal.Vector2D(pos.x + 120, pos.y + 220),
        unreal.Vector2D(900, 420),
    )


def wire_freeaim_drag(editor, bp) -> None:
    mouse_x = find_node(editor, MOUSE_X_NODE)
    mouse_y = find_node(editor, MOUSE_Y_NODE)
    freeaim = find_freeaim_node(editor)
    if not all((mouse_x, mouse_y, freeaim)):
        raise RuntimeError("Missing Mouse X/Y or FreeAimComponent nodes")

    cleanup_freeaim_touch_feed(editor, freeaim, mouse_x, mouse_y)
    cleanup_touch_prev_exec(editor, freeaim)
    ensure_member_vars(editor, bp)

    h_pin = freeaim.find_input_pin("HorizontalMouse")
    v_pin = freeaim.find_input_pin("VerticalMouse")
    if not h_pin or not v_pin:
        raise RuntimeError("FreeAimComponent missing HorizontalMouse/VerticalMouse pins")

    norm_x, norm_y, active = primary_left_touch(editor)
    touch_dx, touch_dy = touch_delta(editor, norm_x, norm_y, active)

    connect_data(add(editor, mouse_x.find_output_pin("ReturnValue"), touch_dx), h_pin)
    connect_data(add(editor, mouse_y.find_output_pin("ReturnValue"), touch_dy), v_pin)
    wire_touch_prev_exec(editor, freeaim, norm_x, norm_y, active)

    tick = editor.find_event_node("ReceiveTick")
    tick_pos = tick.get_node_pos() if tick else unreal.Vector2D(0, 0)
    editor.add_comment_node(
        MARKER,
        unreal.Vector2D(tick_pos.x + 120, tick_pos.y + 900),
        unreal.Vector2D(1400, 500),
    )
    log(
        f"Wired touch delta -> FreeAimComponent while IsAim "
        f"(sens={TOUCH_SENS})"
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
    wire_freeaim_drag(editor, bp)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)
    log("Done — ADS via LeftShift button; hold + drag in left zone moves arms via FreeAim")


main()
