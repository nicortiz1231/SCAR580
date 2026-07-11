"""Patch BP_Laser defaults for AR passthrough: disable IR laser, keep tick enabled."""
import unreal
from pathlib import Path

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/Attachments/Laser/Blueprints/BP_Laser"
BP_ASSET = f"{BP_PATH}.BP_Laser"
LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_bp_laser_ar_visibility.log")


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[fix_bp_laser_ar_visibility] {msg}")


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    bp = unreal.load_asset(BP_ASSET)
    if not bp:
        raise RuntimeError("Missing BP_Laser")

    cdo = unreal.get_default_object(bp.generated_class())
    for prop in ("UseIRLaser",):
        try:
            cdo.set_editor_property(prop, False)
            log(f"Set CDO {prop}=False")
        except Exception as exc:
            log(f"SKIP CDO {prop}: {exc}")

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)
    log("Saved BP_Laser AR visibility defaults")


main()
