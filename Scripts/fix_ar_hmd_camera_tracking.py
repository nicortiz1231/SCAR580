"""Re-enable ARKit automatic camera tracking so the render camera follows the
physical device orientation (bLockToHmd), instead of relying on the abandoned
SCARARPoseSyncComponent (which was never actually attached to BP_FPCharacter).
"""
import unreal
from pathlib import Path

AR_SESSION = "/Game/HandheldAR/D_ARSessionConfig"
BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_ar_hmd_camera_tracking.log")


def log(msg: str) -> None:
    LOG_PATH.write_text((LOG_PATH.read_text() + msg + "\n") if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[fix_ar_hmd_camera_tracking] {msg}")


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


def get_prop(obj, names):
    for name in names:
        try:
            return obj.get_editor_property(name)
        except Exception:
            continue
    return None


def fix_ar_session() -> None:
    config = unreal.load_asset(AR_SESSION)
    if not config:
        raise RuntimeError(f"Missing {AR_SESSION}")
    log(f"Before: bEnableAutomaticCameraTracking={get_prop(config, ('bEnableAutomaticCameraTracking',))}")
    set_prop(config, ("bEnableAutomaticCameraTracking",), True)
    log(f"After: bEnableAutomaticCameraTracking={get_prop(config, ('bEnableAutomaticCameraTracking',))}")
    unreal.EditorAssetLibrary.save_asset(AR_SESSION, only_if_is_dirty=False)


def inspect_and_fix_character() -> None:
    bp = unreal.load_asset(BP_ASSET)
    if not bp:
        raise RuntimeError(f"Missing {BP_ASSET}")

    cdo = unreal.get_default_object(bp.generated_class())
    log(f"bUseControllerRotationYaw={get_prop(cdo, ('bUseControllerRotationYaw',))}")
    log(f"bUseControllerRotationPitch={get_prop(cdo, ('bUseControllerRotationPitch',))}")
    log(f"bUseControllerRotationRoll={get_prop(cdo, ('bUseControllerRotationRoll',))}")

    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = sds.k2_gather_subobject_data_for_blueprint(bp)
    seen = set()
    changed = False
    for handle in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
        if not obj:
            continue
        obj_id = id(obj)
        if obj_id in seen:
            continue
        seen.add(obj_id)

        class_name = obj.get_class().get_name()
        if "CameraComponent" in class_name:
            lock_to_hmd = get_prop(obj, ("lock_to_hmd", "bLockToHmd"))
            log(f"{obj.get_name()} bLockToHmd(before)={lock_to_hmd}")
            if not lock_to_hmd:
                set_prop(obj, ("lock_to_hmd", "bLockToHmd"), True)
                changed = True
        elif "CharacterMovementComponent" in class_name:
            log(f"{obj.get_name()} GravityScale={get_prop(obj, ('gravity_scale', 'GravityScale'))}")

    if changed:
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)
        log("Recompiled + saved BP_FPCharacter")
    else:
        log("No BP_FPCharacter changes needed")


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()
    fix_ar_session()
    inspect_and_fix_character()
    log("Done")


main()
