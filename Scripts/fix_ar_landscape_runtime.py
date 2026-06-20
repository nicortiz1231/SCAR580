"""Force pre-AR landscape camera framing at runtime after bodycam reload."""

import unreal
from pathlib import Path

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
AR_SESSION = "/Game/HandheldAR/D_ARSessionConfig"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_ar_landscape_runtime.log")
MARKER = "AR Landscape Camera Fix"
SET_ASPECT_FN = "/Script/Engine.CameraComponent.SetAspectRatio"
SET_FOV_FN = "/Script/Engine.CameraComponent.SetFieldOfView"


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[fix_ar_landscape_runtime] {msg}")


def set_prop(obj, names, value) -> bool:
    label = obj.get_name() if hasattr(obj, "get_name") else type(obj).__name__
    for name in names:
        try:
            obj.set_editor_property(name, value)
            log(f"Set {label}.{name} = {value}")
            return True
        except Exception as exc:
            log(f"Skip {label}.{name}: {exc}")
    return False


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


def node_title(node) -> str:
    try:
        return str(node.get_node_title(unreal.NodeTitleType.FULL_TITLE)).replace("\n", " | ")
    except Exception:
        return node.get_name()


def fix_camera_template(bp) -> None:
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    seen = set()
    for handle in sds.k2_gather_subobject_data_for_blueprint(bp):
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
        if not obj or "FirstPersonCamera" not in obj.get_name():
            continue
        if id(obj) in seen:
            continue
        seen.add(id(obj))
        set_prop(obj, ("override_aspect_ratio_axis_constraint",), True)
        set_prop(
            obj,
            ("aspect_ratio_axis_constraint",),
            unreal.AspectRatioAxisConstraint.ASPECT_RATIO_MAINTAIN_YFOV,
        )
        set_prop(obj, ("aspect_ratio", "AspectRatio"), 0.0)
        set_prop(obj, ("field_of_view", "FieldOfView"), 90.0)


def configure_ar_session() -> None:
    config = unreal.load_asset(AR_SESSION)
    if not config:
        return
    set_prop(config, ("bEnableAutomaticCameraOverlay",), True)
    set_prop(config, ("bEnableAutomaticCameraTracking",), False)
    unreal.EditorAssetLibrary.save_asset(AR_SESSION, only_if_is_dirty=False)


def camera_fix_already_wired(editor) -> bool:
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
        if "set aspect ratio" not in node_title(node).lower():
            continue
        aspect_pin = node.find_input_pin("InAspectRatio")
        if not aspect_pin:
            continue
        value = unreal.BlueprintGraphPinLibrary.get_pin_value(aspect_pin) or ""
        if value.startswith("0"):
            return True
    return False


def create_camera_fix_chain(editor, anchor_pos: unreal.IntPoint):
    get_camera = editor.add_get_member_variable_node("FirstPersonCamera")
    set_aspect = editor.add_call_function_node(SET_ASPECT_FN)
    set_fov = editor.add_call_function_node(SET_FOV_FN)
    if not get_camera or not set_aspect or not set_fov:
        raise RuntimeError("Failed to create camera fix nodes")

    y = anchor_pos.y + 220
    get_camera.set_node_pos(unreal.IntPoint(anchor_pos.x + 280, y + 120))
    set_aspect.set_node_pos(unreal.IntPoint(anchor_pos.x + 560, y))
    set_fov.set_node_pos(unreal.IntPoint(anchor_pos.x + 840, y))

    cam_out = get_camera.find_output_pin("FirstPersonCamera")
    if not cam_out:
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(get_camera):
            if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) == unreal.EdGraphPinDirection.EGPD_OUTPUT:
                cam_out = pin
                break
    if not cam_out:
        raise RuntimeError("Could not find FirstPersonCamera output pin")

    pin_value(set_aspect.find_input_pin("InAspectRatio"), "0.0")
    pin_value(set_fov.find_input_pin("NewFOV"), "90.0")
    connect_data(cam_out, set_aspect.find_input_pin("self"))
    connect_data(cam_out, set_fov.find_input_pin("self"))
    connect_exec(set_aspect.find_then_pin(), set_fov.find_execute_pin())
    return set_aspect, set_fov


def chain_exec_before(target_exec_pin, first_exec_pin, last_then_pin) -> None:
    upstream = unreal.BlueprintGraphPinLibrary.list_connected_pins(target_exec_pin)
    if not upstream:
        connect_exec(first_exec_pin, target_exec_pin)
        return
    upstream_out = upstream[0]
    unreal.BlueprintGraphPinLibrary.break_pin_links(upstream_out)
    connect_exec(upstream_out, first_exec_pin)
    connect_exec(last_then_pin, target_exec_pin)


def macro_is_begin_setup(node) -> bool:
    if node.get_class().get_name() != "K2Node_MacroInstance":
        return False
    title = node_title(node)
    return "Begin Setup" in title or "BeginSetup" in title.replace(" ", "")


def wire_camera_fix_on_event_graph(bp) -> None:
    event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)
    if camera_fix_already_wired(editor):
        log("Runtime camera fix already wired in EventGraph")
        return

    anchor = unreal.IntPoint(0, 0)
    for node in editor.list_all_nodes():
        if macro_is_begin_setup(node):
            anchor = node.get_node_pos()
            break

    set_aspect, set_fov = create_camera_fix_chain(editor, anchor)
    hooked = False
    for node in editor.list_all_nodes():
        if not macro_is_begin_setup(node):
            continue
        then_pin = node.find_then_pin()
        if not then_pin:
            continue
        downstream = unreal.BlueprintGraphPinLibrary.list_connected_pins(then_pin)
        if downstream:
            chain_exec_before(downstream[0], set_aspect.find_execute_pin(), set_fov.find_then_pin())
        else:
            connect_exec(then_pin, set_aspect.find_execute_pin())
        hooked = True
        log(f"Hooked camera fix after {node.get_name()}")

    if not hooked:
        begin = editor.find_event_node("ReceiveBeginPlay")
        if begin:
            begin_then = begin.find_then_pin()
            existing = unreal.BlueprintGraphPinLibrary.list_connected_pins(begin_then)
            if existing:
                chain_exec_before(existing[0], set_aspect.find_execute_pin(), set_fov.find_then_pin())
            else:
                connect_exec(begin_then, set_aspect.find_execute_pin())
            hooked = True
            log("Hooked camera fix on ReceiveBeginPlay fallback")

    if hooked:
        editor.add_comment_node(
            MARKER,
            unreal.Vector2D(anchor.x + 240, anchor.y - 40),
            unreal.Vector2D(900, 260),
        )


def wire_after_reload_bodycam(bp) -> None:
    graph = None
    for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
        if g.get_name() == "ReloadBodycamSettings":
            graph = g
            break
    if not graph:
        log("ReloadBodycamSettings function not found")
        wire_camera_fix_on_event_graph(bp)
        return

    editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    if camera_fix_already_wired(editor):
        log("Runtime camera fix already wired in ReloadBodycamSettings")
        wire_camera_fix_on_event_graph(bp)
        return

    entry = None
    for node in editor.list_all_nodes():
        if node.get_class().get_name() == "K2Node_FunctionEntry":
            entry = node
            break
    if not entry:
        log("ReloadBodycamSettings entry missing")
        wire_camera_fix_on_event_graph(bp)
        return

    pos = entry.get_node_pos()
    set_aspect, set_fov = create_camera_fix_chain(editor, pos)
    then_pin = entry.find_then_pin()
    downstream = unreal.BlueprintGraphPinLibrary.list_connected_pins(then_pin)
    if downstream:
        chain_exec_before(downstream[0], set_aspect.find_execute_pin(), set_fov.find_then_pin())
    else:
        connect_exec(then_pin, set_aspect.find_execute_pin())
    log("Hooked camera fix at start of ReloadBodycamSettings")
    wire_camera_fix_on_event_graph(bp)


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()
    bp = unreal.load_asset(BP_ASSET)
    if not bp:
        raise RuntimeError(f"Missing {BP_ASSET}")
    fix_camera_template(bp)
    configure_ar_session()
    wire_after_reload_bodycam(bp)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)
    log("Done - landscape uses viewport Y-FOV at runtime")


main()
