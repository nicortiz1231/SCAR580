"""The multiplayer game mode actually starts AR sessions with
D_ARSessionConfig_BodyTracking (not D_ARSessionConfig). Ensure automatic
camera tracking is enabled on the config that is ACTUALLY used at runtime.
"""
import unreal
from pathlib import Path

AR_SESSION = "/Game/SCAR580/D_ARSessionConfig_BodyTracking"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_ar_body_tracking_camera_tracking.log")


def log(msg: str) -> None:
    LOG_PATH.write_text((LOG_PATH.read_text() + msg + "\n") if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[fix_ar_body_tracking_camera_tracking] {msg}")


def get_prop(obj, names):
    for name in names:
        try:
            return obj.get_editor_property(name)
        except Exception:
            continue
    return None


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


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    config = unreal.load_asset(AR_SESSION)
    if not config:
        raise RuntimeError(f"Missing {AR_SESSION}")

    for prop in (
        "bEnableAutomaticCameraTracking",
        "bEnableAutomaticCameraOverlay",
        "bResetCameraTracking",
        "session_type",
        "SessionType",
    ):
        log(f"Before {prop}={get_prop(config, (prop,))}")

    set_prop(config, ("bEnableAutomaticCameraTracking",), True)

    for prop in ("bEnableAutomaticCameraTracking",):
        log(f"After {prop}={get_prop(config, (prop,))}")

    unreal.EditorAssetLibrary.save_asset(AR_SESSION, only_if_is_dirty=False)
    log("Saved " + AR_SESSION)


main()
