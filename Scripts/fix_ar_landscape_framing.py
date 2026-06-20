"""Subtle landscape-only weapon framing wired on BP_FPCharacter ReceiveTick."""

import unreal
from pathlib import Path

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
MARKER_COMMENT = "AR Landscape Framing"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_ar_landscape_framing.log")

# Subtle nudge: pitch-only (SetSocketOffset unavailable via graph editor API).
LANDSCAPE_PITCH = 2.5


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[fix_ar_landscape_framing] {msg}")


def pin_value(pin, value: str) -> None:
    if pin:
        pin.set_pin_value(value)


def connect_exec(src, dst) -> None:
    if not src.try_create_connection(dst):
        raise RuntimeError("Exec connection failed")


def connect_data(src, dst) -> None:
    if not src.try_create_connection(dst):
        raise RuntimeError("Data connection failed")


def already_wired(editor) -> bool:
    for node in editor.list_all_nodes():
        if node.get_class().get_name() != "K2Node_CallFunction":
            continue
        rot_pin = node.find_input_pin("NewRotation")
        if not rot_pin:
            continue
        value = unreal.BlueprintGraphPinLibrary.get_pin_value(rot_pin)
        if f"Pitch={LANDSCAPE_PITCH:.6f}" in value:
            return True
    return False


def remove_orphan_function(bp) -> None:
    for graph in unreal.BlueprintEditorLibrary.list_graphs(bp):
        if graph.get_name() == "UpdateLandscapeFraming":
            unreal.BlueprintEditorLibrary.remove_function_graph(bp, "UpdateLandscapeFraming")
            log("Removed unused UpdateLandscapeFraming function graph")
            return


def wire_landscape_framing(bp) -> None:
    event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)

    if already_wired(editor):
        log("Landscape framing already present in EventGraph")
        return

    tick = editor.find_event_node("ReceiveTick")
    if not tick:
        raise RuntimeError("ReceiveTick event missing on BP_FPCharacter")

    get_viewport = editor.add_call_function_node("/Script/UMG.WidgetLayoutLibrary.GetViewportSize")
    break_vec = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.BreakVector2D")
    get_spring = editor.add_get_member_variable_node("SpringArm")
    gt = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.Greater_IntInt")
    branch = editor.add_branch_node()
    set_landscape_rot = editor.add_call_function_node("/Script/Engine.SceneComponent.K2_SetRelativeRotation")
    set_portrait_rot = editor.add_call_function_node("/Script/Engine.SceneComponent.K2_SetRelativeRotation")

    required = (
        get_viewport,
        break_vec,
        get_spring,
        gt,
        branch,
        set_landscape_rot,
        set_portrait_rot,
    )
    if any(x is None for x in required):
        missing = [name for name, node in zip(
            (
                "get_viewport",
                "break_vec",
                "get_spring",
                "gt",
                "branch",
                "set_landscape_rot",
                "set_portrait_rot",
            ),
            required,
        ) if node is None]
        raise RuntimeError(f"Failed to create nodes: {missing}")

    tick_pos = tick.get_node_pos()
    get_viewport.set_node_pos(unreal.IntPoint(tick_pos.x + 320, tick_pos.y + 260))
    break_vec.set_node_pos(unreal.IntPoint(tick_pos.x + 600, tick_pos.y + 260))
    gt.set_node_pos(unreal.IntPoint(tick_pos.x + 860, tick_pos.y + 260))
    branch.set_node_pos(unreal.IntPoint(tick_pos.x + 1100, tick_pos.y + 260))
    get_spring.set_node_pos(unreal.IntPoint(tick_pos.x + 320, tick_pos.y + 480))
    set_landscape_rot.set_node_pos(unreal.IntPoint(tick_pos.x + 1400, tick_pos.y + 180))
    set_portrait_rot.set_node_pos(unreal.IntPoint(tick_pos.x + 1400, tick_pos.y + 380))

    pin_value(get_viewport.find_input_pin("WorldContextObject"), "self")

    connect_data(get_viewport.find_output_pin("ReturnValue"), break_vec.find_input_pin("InVec"))
    connect_data(break_vec.find_output_pin("X"), gt.find_input_pin("A"))
    connect_data(break_vec.find_output_pin("Y"), gt.find_input_pin("B"))
    connect_data(gt.find_output_pin("ReturnValue"), branch.find_input_pin("Condition"))

    spring_out = get_spring.find_output_pin("SpringArm")
    connect_data(spring_out, set_landscape_rot.find_input_pin("self"))
    connect_data(spring_out, set_portrait_rot.find_input_pin("self"))

    pin_value(
        set_landscape_rot.find_input_pin("NewRotation"),
        f"(Pitch={LANDSCAPE_PITCH:.6f},Yaw=0.000000,Roll=0.000000)",
    )
    pin_value(set_portrait_rot.find_input_pin("NewRotation"), "(Pitch=0.000000,Yaw=0.000000,Roll=0.000000)")

    tick_then = tick.find_then_pin()
    existing = unreal.BlueprintGraphPinLibrary.list_connected_pins(tick_then)
    if existing:
        seq_node = editor.create_node_from_name(
            "Utilities|FlowControl|Sequence",
            unreal.Vector2D(tick_pos.x + 160, tick_pos.y + 260),
            [],
        )
        if not seq_node:
            raise RuntimeError("ReceiveTick already wired and could not insert Sequence node")

        unreal.BlueprintGraphPinLibrary.break_pin_links(tick_then)
        connect_exec(tick_then, seq_node.find_execute_pin())
        connect_exec(seq_node.find_output_pin("then_0"), branch.find_execute_pin())
        connect_exec(seq_node.find_output_pin("then_1"), existing[0])
    else:
        connect_exec(tick_then, branch.find_execute_pin())

    connect_exec(branch.find_then_pin(), set_landscape_rot.find_execute_pin())
    connect_exec(branch.find_else_pin(), set_portrait_rot.find_execute_pin())

    editor.add_comment_node(
        MARKER_COMMENT,
        unreal.Vector2D(tick_pos.x + 280, tick_pos.y + 120),
        unreal.Vector2D(1300, 420),
    )

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    log(f"Wired ReceiveTick landscape framing (pitch +{LANDSCAPE_PITCH}, portrait reset)")


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    bp = unreal.load_asset(BP_ASSET)
    if not bp:
        raise RuntimeError(f"Missing {BP_ASSET}")

    remove_orphan_function(bp)
    wire_landscape_framing(bp)
    unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)
    log("Done - redeploy to iPhone and check landscape weapon position")


main()
