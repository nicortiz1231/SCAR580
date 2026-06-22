"""Configure AR body detection (ARKit 3D/Pose2D + Apple Vision) for SCAR-580."""

import unreal
from pathlib import Path

LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/setup_ar_body_detection.log")

AR_SESSION = "/Game/HandheldAR/D_ARSessionConfig"
AR_SESSION_BODY = "/Game/SCAR580/D_ARSessionConfig_BodyTracking"
AR_SESSION_BODY_ASSET = f"{AR_SESSION_BODY}.D_ARSessionConfig_BodyTracking"
GM_AR = "/Game/SCAR580/Blueprints/GameModes/GM_SCAR_AR"
MAP_AR = "/Game/SCAR580/Maps/Map_AR"
START_FN = "/Script/AugmentedReality.ARBlueprintLibrary.StartARSession"
DEBUG_ACTOR_CLASS = "/Script/SCAR.SCARBodyDebugActor"


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[setup_ar_body_detection] {msg}")


def ensure_directory(path: str) -> None:
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)
        log(f"Created directory {path}")


def set_prop(obj, names, value) -> bool:
    for name in names:
        try:
            obj.set_editor_property(name, value)
            log(f"Set {obj.get_name()}.{name} = {value}")
            return True
        except Exception as exc:
            log(f"Skip {name}: {exc}")
    return False


def resolve_pose_detection_2d():
    for enum_name in ("ARSessionTrackingFeature", "EARSessionTrackingFeature"):
        enum_cls = getattr(unreal, enum_name, None)
        if not enum_cls:
            continue
        for value_name in ("POSE_DETECTION2D", "POSE_DETECTION_2D"):
            value = getattr(enum_cls, value_name, None)
            if value is not None:
                log(f"Resolved tracking feature enum: {enum_name}.{value_name}")
                return value
    raise RuntimeError("Could not resolve PoseDetection2D on unreal.ARSessionTrackingFeature")


def configure_body_tracking_session() -> None:
    ensure_directory("/Game/SCAR580")

    if not unreal.EditorAssetLibrary.does_asset_exist(AR_SESSION):
        raise RuntimeError(f"Missing base AR session config at {AR_SESSION}")

    if unreal.EditorAssetLibrary.does_asset_exist(AR_SESSION_BODY):
        config = unreal.load_asset(AR_SESSION_BODY)
        log(f"Updating existing body tracking session at {AR_SESSION_BODY}")
    else:
        config = unreal.EditorAssetLibrary.duplicate_asset(AR_SESSION, AR_SESSION_BODY)
        if not config:
            raise RuntimeError(f"Failed to duplicate {AR_SESSION} -> {AR_SESSION_BODY}")
        log(f"Duplicated body tracking session config to {AR_SESSION_BODY}")

    # ARBodyTrackingConfiguration parity (Unity ARHumanBodyManager): 3D body + device tracking.
    set_prop(config, ("session_type",), unreal.ARSessionType.POSE_TRACKING)
    set_prop(config, ("enabled_session_tracking_feature", "EnabledSessionTrackingFeature"),
             resolve_pose_detection_2d())
    set_prop(config, ("b_enable_automatic_camera_overlay", "bEnableAutomaticCameraOverlay"), True)
    set_prop(config, ("b_enable_automatic_camera_tracking", "bEnableAutomaticCameraTracking"), False)
    set_prop(config, ("b_horizontal_plane_detection", "bHorizontalPlaneDetection"), True)
    set_prop(config, ("b_vertical_plane_detection", "bVerticalPlaneDetection"), False)
    set_prop(config, ("b_enable_auto_focus", "bEnableAutoFocus"), True)
    set_prop(config, ("b_reset_camera_tracking", "bResetCameraTracking"), True)
    set_prop(config, ("b_reset_tracked_objects", "bResetTrackedObjects"), True)
    set_prop(config, ("b_generate_mesh_data_from_tracked_geometry", "bGenerateMeshDataFromTrackedGeometry"), False)

    unreal.EditorAssetLibrary.save_asset(AR_SESSION_BODY, only_if_is_dirty=False)


def node_title(node) -> str:
    try:
        return str(node.get_node_title(unreal.NodeTitleType.FULL_TITLE)).replace("\n", " | ")
    except Exception:
        return node.get_name()


def node_calls_start_ar_session(node) -> bool:
    if node.get_class().get_name() != "K2Node_CallFunction":
        return False
    for prop in ("function_reference", "FunctionReference"):
        try:
            fn_ref = str(node.get_editor_property(prop))
            if "StartARSession" in fn_ref:
                return True
        except Exception:
            pass
    return "start ar session" in node_title(node).lower()


def set_session_config_pin(node, session_asset_path: str) -> bool:
    config_pin = node.find_input_pin("SessionConfig")
    if not config_pin:
        return False
    config_pin.set_pin_value(session_asset_path)
    log(f"Set {node.get_name()} SessionConfig = {session_asset_path}")
    return True


def wire_game_mode_to_body_session() -> None:
    gm_bp = unreal.load_asset(f"{GM_AR}.GM_SCAR_AR")
    if not gm_bp:
        raise RuntimeError(f"Missing game mode {GM_AR}")

    if not unreal.EditorAssetLibrary.does_asset_exist(AR_SESSION_BODY):
        raise RuntimeError(f"Missing body tracking session {AR_SESSION_BODY}")

    event_graph = unreal.BlueprintEditorLibrary.find_event_graph(gm_bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)

    rewired = False
    for node in editor.list_all_nodes():
        if not node_calls_start_ar_session(node):
            continue
        if set_session_config_pin(node, AR_SESSION_BODY_ASSET):
            rewired = True

    if not rewired:
        begin = editor.find_event_node("ReceiveBeginPlay")
        if not begin:
            raise RuntimeError("GM_SCAR_AR missing ReceiveBeginPlay event")

        start_node = editor.add_call_function_node(START_FN)
        if not start_node:
            raise RuntimeError(f"Failed to create node for {START_FN}")
        if not set_session_config_pin(start_node, AR_SESSION_BODY_ASSET):
            raise RuntimeError("Start AR Session node missing SessionConfig pin")

        if not begin.find_then_pin().try_create_connection(start_node.find_execute_pin()):
            raise RuntimeError("Failed to connect BeginPlay to Start AR Session")

        begin_pos = begin.get_node_pos()
        start_node.set_node_pos(unreal.IntPoint(begin_pos.x + 320, begin_pos.y))
        log("Wired GM_SCAR_AR BeginPlay -> Start AR Session (body tracking config)")

    unreal.BlueprintEditorLibrary.compile_blueprint(gm_bp)
    unreal.EditorAssetLibrary.save_asset(GM_AR, only_if_is_dirty=False)
    log("Saved GM_SCAR_AR with body tracking session")


def ensure_debug_actor_in_map() -> None:
    debug_class = getattr(unreal, "SCARBodyDebugActor", None)
    if debug_class:
        debug_class = debug_class.static_class()
    else:
        debug_class = unreal.load_class(None, DEBUG_ACTOR_CLASS)
    if not debug_class:
        log("SCARBodyDebugActor class not compiled yet; skip map placement (re-run after C++ build)")
        return

    if not unreal.EditorAssetLibrary.does_asset_exist(MAP_AR):
        log(f"Map {MAP_AR} not found; skip debug actor placement")
        return

    unreal.EditorLoadingAndSavingUtils.load_map(MAP_AR)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not world:
        log("Editor world unavailable")
        return

    existing = [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, debug_class)]
    if existing:
        log(f"SCARBodyDebugActor already present: {existing[0].get_name()}")
        return

    editor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = editor_subsystem.spawn_actor_from_class(
        debug_class,
        unreal.Vector(0.0, 0.0, 0.0),
        unreal.Rotator(0.0, 0.0, 0.0),
    )
    actor.set_actor_label("AR_BodyDebug")
    log(f"Spawned {actor.get_name()} in Map_AR")
    unreal.EditorLoadingAndSavingUtils.save_map(unreal.load_asset(MAP_AR), MAP_AR)


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    configure_body_tracking_session()
    wire_game_mode_to_body_session()
    ensure_debug_actor_in_map()
    log("AR body detection setup complete")


main()
