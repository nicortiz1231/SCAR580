"""Disable bLockToHmd on FirstPersonCamera. Camera rotation is now driven by
ASCARARMultiplayerPlayerController::PlayerTick setting ControlRotation from a
smoothed AR device pose each frame (via bUsePawnControlRotation), which keeps
the camera and the arm/weapon IK (also reading ControlRotation) in sync.
bLockToHmd would otherwise override the camera's final transform directly
from the raw, unsmoothed device pose every frame, undoing that sync.
"""
import unreal
from pathlib import Path

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_ar_disable_lock_to_hmd.log")


def log(msg: str) -> None:
    with LOG_PATH.open("a") as f:
        f.write(str(msg) + "\n")
    unreal.log(f"[fix_ar_disable_lock_to_hmd] {msg}")


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    bp = unreal.load_asset(BP_ASSET)
    if not bp:
        raise RuntimeError(f"Missing {BP_ASSET}")

    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    found = False
    for handle in sds.k2_gather_subobject_data_for_blueprint(bp):
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
        if not obj or "FirstPersonCamera" not in obj.get_name():
            continue
        if "CameraComponent" not in obj.get_class().get_name():
            continue
        found = True
        try:
            before = obj.get_editor_property("lock_to_hmd")
        except Exception as exc:
            before = f"ERR {exc}"
        log(f"before bLockToHmd = {before}")
        try:
            obj.set_editor_property("lock_to_hmd", False)
            log("Set FirstPersonCamera.bLockToHmd = False")
        except Exception as exc:
            log(f"FAILED to set lock_to_hmd: {exc}")
        try:
            obj.set_editor_property("use_pawn_control_rotation", True)
            log("Confirmed bUsePawnControlRotation = True")
        except Exception as exc:
            log(f"FAILED to set use_pawn_control_rotation: {exc}")

    if not found:
        raise RuntimeError("FirstPersonCamera not found")

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)
    log("Compiled and saved BP_FPCharacter")


main()
