"""Set AR session configs to World tracking so iPhone walking translates XYZ."""

import unreal
from pathlib import Path

LOG = Path(__file__).resolve().parent / "fix_ar_world_tracking.log"

CONFIGS = [
    "/Game/SCAR580/D_ARSessionConfig_BodyTracking",
    "/Game/HandheldAR/D_ARSessionConfig",
]


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[fix_ar_world_tracking] {msg}")


def set_world_tracking(config_path: str) -> None:
    asset = unreal.load_asset(config_path)
    if not asset:
        log(f"MISSING {config_path}")
        return

    asset.set_editor_property("session_type", unreal.ARSessionType.WORLD)
    asset.set_editor_property("enable_auto_focus", True)

    for prop, value in (
        ("b_enable_automatic_camera_tracking", True),
        ("b_enable_automatic_camera_overlay", True),
        ("b_horizontal_plane_detection", True),
        ("b_vertical_plane_detection", False),
    ):
        try:
            asset.set_editor_property(prop, value)
        except Exception as exc:
            log(f"  skip {prop}: {exc}")

    unreal.EditorAssetLibrary.save_asset(config_path, only_if_is_dirty=False)
    log(f"World tracking: {config_path}")


def main() -> None:
    LOG.write_text("")
    for path in CONFIGS:
        set_world_tracking(path)
    log("Done.")


if __name__ == "__main__":
    main()
