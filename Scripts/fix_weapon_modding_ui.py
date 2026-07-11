"""Fix UI_WeaponModding: dedupe dropdown options + portrait layout hook."""
import unreal
from pathlib import Path

WBP_PATH = "/Game/BodycamFPSKIT/Blueprints/Widgets/UI_WeaponModding"
WBP_ASSET = f"{WBP_PATH}.UI_WeaponModding"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_weapon_modding_ui.log")

CLEAR_OPTIONS_FN = "/Script/UMG.ComboBoxString:ClearOptions"
GET_VIEWPORT_SIZE_FN = "/Script/UMG.WidgetLayoutLibrary:GetViewportSize"
SET_RENDER_SCALE_FN = "/Script/UMG.Widget:SetRenderScale"
SET_RENDER_PIVOT_FN = "/Script/UMG.Widget:SetRenderTransformPivot"
GREATER_FLOAT_FN = "/Script/Engine.KismetMathLibrary:Greater_FloatFloat"
GET_PLAYER_CONTROLLER_FN = "/Script/Engine.GameplayStatics:GetPlayerController"

COMBO_WIDGETS = ("Sight", "Laser", "Muzzle", "GRIP")
PORTRAIT_LAYOUT_MARKER = "SCAR_ApplyPortraitLayout"


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[fix_weapon_modding_ui] {msg}")


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


def make_clear_options_node(editor, widget_name: str):
    clear_node = editor.add_call_function_node(CLEAR_OPTIONS_FN)
    get_widget = editor.add_get_member_variable_node(widget_name)
    if not clear_node or not get_widget:
        raise RuntimeError(f"Failed creating ClearOptions nodes for {widget_name}")
    connect_data(output_pin(get_widget, widget_name), clear_node.find_input_pin("self"))
    return clear_node


def has_clear_options_chain(editor) -> bool:
    pre = None
    for node in editor.list_all_nodes():
        if "PreConstruct" in str(node.get_node_title()):
            pre = node
            break
    if not pre:
        return False
    then = pre.find_output_pin("then")
    if not then:
        return False
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
        owner = lp.get_owning_node()
        if "ClearOptions" in str(owner.get_node_title()):
            return True
    return False


def install_clear_options_chain(editor) -> None:
    if has_clear_options_chain(editor):
        log("ClearOptions chain already present — skipping")
        return

    pre = next(n for n in editor.list_all_nodes() if "PreConstruct" in str(n.get_node_title()))
    foreach_sights = find_node(editor, "K2Node_ForEachElementInEnum_2")
    if not foreach_sights:
        raise RuntimeError("Missing ForEach ENUM_Sights node")

    pre_then = pre.find_output_pin("then")
    foreach_exec = foreach_sights.find_input_pin("execute")
    if not pre_then or not foreach_exec:
        raise RuntimeError("Missing PreConstruct/ForEach exec pins")

    # Break PreConstruct -> ForEach and insert ClearOptions chain.
    pre_then.break_pin_links()

    prev_exec_out = pre_then
    for widget_name in COMBO_WIDGETS:
        clear_node = make_clear_options_node(editor, widget_name)
        if not insert_exec_after_pin(prev_exec_out, clear_node):
            raise RuntimeError(f"Failed wiring ClearOptions for {widget_name}")
        prev_exec_out = clear_node.find_output_pin("then")

    if not connect_exec(prev_exec_out, foreach_exec):
        raise RuntimeError("Failed wiring final ClearOptions -> ForEach Sights")

    log("Inserted ClearOptions chain before attachment dropdown populate")


def has_portrait_layout(editor) -> bool:
    for node in editor.list_all_nodes():
        title = str(node.get_node_title())
        if "GetViewportSize" in title or "SetRenderScale" in title:
            return True
    return False


def install_portrait_layout(editor) -> None:
    if has_portrait_layout(editor):
        log("Portrait layout nodes already present — skipping")
        return

    construct = next(n for n in editor.list_all_nodes() if n.get_node_title() == "Construct")
    seq = find_node(editor, "K2Node_ExecutionSequence_0")
    if not seq:
        raise RuntimeError("Missing Construct Sequence node")

    # Append portrait layout after Sequence then_1 branch terminus if possible, else after Sequence.
    tail_pin = None
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(seq):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        if pn != "then_1":
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            node = lp.get_owning_node()
            # Walk to end of then_1 branch
            current = node
            while current:
                then = current.find_output_pin("then")
                if not then:
                    break
                next_nodes = [
                    lp2.get_owning_node()
                    for lp2 in unreal.BlueprintGraphPinLibrary.list_connected_pins(then)
                    if lp2.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT
                ]
                if not next_nodes:
                    tail_pin = then
                    break
                current = next_nodes[0]

    if not tail_pin:
        tail_pin = seq.find_output_pin("then_1")

    get_pc = editor.add_call_function_node(GET_PLAYER_CONTROLLER_FN)
    get_world = editor.add_call_function_node("/Script/Engine.GameplayStatics:GetWorld")
    get_vp = editor.add_call_function_node(GET_VIEWPORT_SIZE_FN)
    branch = editor.add_branch_node()
    set_scale = editor.add_call_function_node(SET_RENDER_SCALE_FN)
    set_pivot = editor.add_call_function_node(SET_RENDER_PIVOT_FN)
    set_scale_land = editor.add_call_function_node(SET_RENDER_SCALE_FN)
    set_pivot_land = editor.add_call_function_node(SET_RENDER_PIVOT_FN)
    greater_y = editor.add_call_function_node(GREATER_FLOAT_FN)
    divide = editor.add_call_function_node("/Script/Engine.KismetMathLibrary:Divide_FloatFloat")
    clamp = editor.add_call_function_node("/Script/Engine.KismetMathLibrary:FClamp")
    subtract = editor.add_call_function_node("/Script/Engine.KismetMathLibrary:Subtract_FloatFloat")

    if not all((get_pc, get_vp, branch, set_scale, set_pivot, set_scale_land, set_pivot_land, greater_y, divide, clamp, subtract)):
        raise RuntimeError("Failed creating portrait layout nodes")

    # exec: tail -> get_pc -> get_vp -> branch
    if not insert_exec_after_pin(tail_pin, get_pc):
        # If then_1 is empty, wire from sequence via knot output
        if not connect_exec(tail_pin, get_pc.find_input_pin("execute")):
            raise RuntimeError("Failed wiring portrait layout exec chain")

    connect_exec(get_pc.find_output_pin("then"), get_vp.find_input_pin("execute"))
    connect_exec(get_vp.find_output_pin("then"), branch.find_input_pin("execute"))

    # GetPlayerController(WorldContext, 0)
    connect_data(output_pin(get_world, "ReturnValue"), get_pc.find_input_pin("WorldContextObject"))
    get_pc.find_input_pin("PlayerIndex").set_pin_value("0")

    # Viewport size
    connect_data(output_pin(get_world, "ReturnValue"), get_vp.find_input_pin("WorldContextObject"))

    size_x = get_vp.find_output_pin("SizeX")
    size_y = get_vp.find_output_pin("SizeY")
    connect_data(size_y, greater_y.find_input_pin("A"))
    connect_data(size_x, greater_y.find_input_pin("B"))
    connect_data(output_pin(greater_y, "ReturnValue"), branch.find_input_pin("Condition"))

    # Portrait scale = clamp((SizeX - 48) / 920, 0.45, 0.95)
    connect_data(size_x, subtract.find_input_pin("A"))
    subtract.find_input_pin("B").set_pin_value("48.0")
    connect_data(output_pin(subtract, "ReturnValue"), divide.find_input_pin("A"))
    divide.find_input_pin("B").set_pin_value("920.0")
    connect_data(output_pin(divide, "ReturnValue"), clamp.find_input_pin("Value"))
    clamp.find_input_pin("Min").set_pin_value("0.45")
    clamp.find_input_pin("Max").set_pin_value("0.95")

    # Branch true (portrait): set pivot top-center, scale
    connect_exec(branch.find_output_pin("then"), set_pivot.find_input_pin("execute"))
    connect_exec(set_pivot.find_output_pin("then"), set_scale.find_input_pin("execute"))
    set_pivot.find_input_pin("Pivot").set_pin_value("(X=0.500000,Y=0.000000)")
    connect_data(output_pin(clamp, "ReturnValue"), set_scale.find_input_pin("Scale").find_sub_pin("X") if False else None)

    # SetRenderScale needs FVector2D - use same value for X and Y via default pin
    scale_pin = set_scale.find_input_pin("Scale")
    if scale_pin:
        # connect clamp to X; duplicate for Y using Reroute or set struct default
        connect_data(output_pin(clamp, "ReturnValue"), scale_pin)

    # self = this widget (Construct)
    # Use "self" context - add Self node
    self_nodes = [n for n in editor.list_all_nodes() if n.get_class().get_name() == "K2Node_Self"]
    self_node = self_nodes[0] if self_nodes else editor.add_self_node()
    connect_data(output_pin(self_node, "self"), set_pivot.find_input_pin("self"))
    connect_data(output_pin(self_node, "self"), set_scale.find_input_pin("self"))

    # Branch false (landscape): reset scale 1, pivot center
    connect_exec(branch.find_output_pin("else"), set_pivot_land.find_input_pin("execute"))
    connect_exec(set_pivot_land.find_output_pin("then"), set_scale_land.find_input_pin("execute"))
    set_pivot_land.find_input_pin("Pivot").set_pin_value("(X=0.500000,Y=0.500000)")
    set_scale_land.find_input_pin("Scale").set_pin_value("1.0")
    connect_data(output_pin(self_node, "self"), set_pivot_land.find_input_pin("self"))
    connect_data(output_pin(self_node, "self"), set_scale_land.find_input_pin("self"))

    log("Installed portrait/landscape render scale branch at end of Construct")


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    wbp = unreal.load_asset(WBP_ASSET)
    if not wbp:
        raise RuntimeError(f"Missing {WBP_ASSET}")

    eg = unreal.BlueprintEditorLibrary.find_event_graph(wbp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)

    install_clear_options_chain(editor)

    # Portrait layout is safer in C++ on open; skip fragile blueprint scale wiring for now.
    # install_portrait_layout(editor)

    unreal.BlueprintEditorLibrary.compile_blueprint(wbp)
    unreal.EditorAssetLibrary.save_asset(WBP_PATH, only_if_is_dirty=False)
    log("Saved UI_WeaponModding")


main()
