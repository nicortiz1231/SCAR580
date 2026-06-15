"""Restore AR-era smooth FPS arm movement on BP_FPCharacter."""

import unreal
from pathlib import Path

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR/Scripts/fix_ar_smooth_arms.log")


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[fix_ar_smooth_arms] {msg}")


def set_if_exists(obj, prop_names, value) -> bool:
    for prop in prop_names:
        try:
            obj.set_editor_property(prop, value)
            log(f"Set {obj.get_name()}.{prop} = {value}")
            return True
        except Exception as exc:
            log(f"Failed {prop} on {obj.get_name()}: {exc}")
    return False


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    bp = unreal.load_asset(BP_ASSET) or unreal.load_asset(BP_PATH)
    if not bp:
        raise RuntimeError(f"Failed to load {BP_PATH}")

    cdo = unreal.get_default_object(bp.generated_class())
    set_if_exists(cdo, ("BODYCAM",), True)

    movement_found = False
    spring_found = False
    comps = cdo.get_components_by_class(unreal.ActorComponent.static_class())
    log(f"Found {len(comps)} components on CDO")
    for comp in comps:
        class_name = comp.get_class().get_name()
        log(f"Component: {comp.get_name()} ({class_name})")
        if "CharacterMovementComponent" in class_name:
            movement_found = set_if_exists(comp, ("gravity_scale", "GravityScale"), 0.0) or movement_found
        if "SpringArmComponent" in class_name:
            set_if_exists(comp, ("enable_camera_lag", "b_enable_camera_lag"), False)
            set_if_exists(comp, ("enable_camera_rotation_lag", "b_enable_camera_rotation_lag"), False)
            spring_found = True

    if not movement_found:
        raise RuntimeError("CharacterMovement component not found on CDO")
    if not spring_found:
        log("Warning: SpringArm not found on CDO")

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)
    log("Compiled and saved BP_FPCharacter")


main()
