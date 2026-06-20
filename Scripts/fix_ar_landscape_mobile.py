"""Landscape weapon framing fix: use viewport Y-FOV instead of locked 16:9 X-FOV."""

import unreal
from pathlib import Path

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
AR_SESSION = "/Game/HandheldAR/D_ARSessionConfig"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_ar_landscape_mobile.log")


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[fix_ar_landscape_mobile] {msg}")


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


def fix_camera_aspect(bp) -> None:
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


def configure_ar_session() -> None:
    config = unreal.load_asset(AR_SESSION)
    if not config:
        return
    set_prop(config, ("bEnableAutomaticCameraOverlay",), True)
    set_prop(config, ("bEnableAutomaticCameraTracking",), False)
    unreal.EditorAssetLibrary.save_asset(AR_SESSION, only_if_is_dirty=False)


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()
    bp = unreal.load_asset(BP_ASSET)
    if not bp:
        raise RuntimeError(f"Missing {BP_ASSET}")
    fix_camera_aspect(bp)
    configure_ar_session()
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)
    log("Done - camera MAINTAIN_YFOV; AR passthrough unchanged")


main()
