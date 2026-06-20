"""Enable AR camera passthrough by starting the AR session at game start."""
import unreal
from pathlib import Path

GM_AR = "/Game/SCAR580/Blueprints/GameModes/GM_SCAR_AR"
AR_SESSION = "/Game/HandheldAR/D_ARSessionConfig"
AR_SESSION_ASSET = f"{AR_SESSION}.D_ARSessionConfig"
START_FN = "/Script/AugmentedReality.ARBlueprintLibrary.StartARSession"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_ar_camera_preview.log")


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[fix_ar_camera_preview] {msg}")


def set_prop(obj, names, value) -> bool:
    for name in names:
        try:
            obj.set_editor_property(name, value)
            log(f"Set {obj.get_name()}.{name} = {value}")
            return True
        except Exception as exc:
            log(f"Skip {obj.get_name()}.{name}: {exc}")
    return False


def configure_ar_session_config() -> None:
    config = unreal.load_asset(AR_SESSION)
    if not config:
        raise RuntimeError(f"Missing {AR_SESSION}")
    set_prop(config, ("bEnableAutomaticCameraOverlay",), True)
    set_prop(config, ("bEnableAutomaticCameraTracking",), False)
    unreal.EditorAssetLibrary.save_asset(AR_SESSION, only_if_is_dirty=False)


def node_calls_start_ar_session(node) -> bool:
    if node.get_class().get_name() != "K2Node_CallFunction":
        return False
    fn_ref = str(node.get_editor_property("function_reference"))
    if "StartARSession" not in fn_ref:
        return False
    config_pin = node.find_input_pin("SessionConfig")
    if not config_pin:
        return False
    value = unreal.BlueprintGraphPinLibrary.get_pin_value(config_pin)
    return "D_ARSessionConfig" in value


def begin_play_starts_ar_session(editor) -> bool:
    begin = editor.find_event_node("ReceiveBeginPlay")
    if not begin:
        return False
    then_pin = begin.find_then_pin()
    if not then_pin:
        return False
    for linked in then_pin.get_linked_to():
        target = linked.get_owning_node()
        if target and node_calls_start_ar_session(target):
            return True
    return False


def wire_start_ar_session(gm_bp) -> None:
    event_graph = unreal.BlueprintEditorLibrary.find_event_graph(gm_bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)

    if begin_play_starts_ar_session(editor):
        log("GM_SCAR_AR BeginPlay already wired to Start AR Session")
        return

    begin = editor.find_event_node("ReceiveBeginPlay")
    if not begin:
        raise RuntimeError("GM_SCAR_AR missing ReceiveBeginPlay event")

    start_node = editor.add_call_function_node(START_FN)
    if not start_node:
        raise RuntimeError(f"Failed to create node for {START_FN}")

    config_pin = start_node.find_input_pin("SessionConfig")
    if not config_pin:
        raise RuntimeError("Start AR Session node missing SessionConfig pin")
    config_pin.set_pin_value(AR_SESSION_ASSET)
    log(f"Set SessionConfig = {AR_SESSION_ASSET}")

    if not begin.find_then_pin().try_create_connection(start_node.find_execute_pin()):
        raise RuntimeError("Failed to connect BeginPlay to Start AR Session")

    begin_pos = begin.get_node_pos()
    start_node.set_node_pos(unreal.IntPoint(begin_pos.x + 320, begin_pos.y))
    log("Wired GM_SCAR_AR BeginPlay -> Start AR Session")

    unreal.BlueprintEditorLibrary.compile_blueprint(gm_bp)


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    configure_ar_session_config()

    gm_bp = unreal.load_asset(f"{GM_AR}.GM_SCAR_AR")
    if not gm_bp:
        raise RuntimeError(f"Missing {GM_AR}")
    wire_start_ar_session(gm_bp)
    unreal.EditorAssetLibrary.save_asset(GM_AR, only_if_is_dirty=False)
    log("Saved GM_SCAR_AR")
    log("Done - redeploy to iPhone to verify AR camera preview")


main()
