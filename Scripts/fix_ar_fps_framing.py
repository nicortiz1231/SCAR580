"""Restore original Bodycam FPS arm/weapon framing (pre AR framing tweak)."""

import unreal
from pathlib import Path

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_ar_fps_framing.log")


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[fix_ar_fps_framing] {msg}")


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


def configure_post_process_settings(settings, label: str) -> None:
    set_prop(settings, ("override_auto_exposure_method", "b_override_auto_exposure_method"), True)
    set_prop(settings, ("auto_exposure_method",), unreal.AutoExposureMethod.AEM_MANUAL)
    set_prop(settings, ("override_auto_exposure_bias", "b_override_auto_exposure_bias"), True)
    set_prop(settings, ("auto_exposure_bias",), 1.0)
    set_prop(settings, ("override_auto_exposure_min_brightness", "b_override_auto_exposure_min_brightness"), True)
    set_prop(settings, ("auto_exposure_min_brightness",), 1.0)
    set_prop(settings, ("override_auto_exposure_max_brightness", "b_override_auto_exposure_max_brightness"), True)
    set_prop(settings, ("auto_exposure_max_brightness",), 1.0)
    set_prop(settings, ("override_auto_exposure_apply_physical_camera_exposure",), True)
    set_prop(settings, ("auto_exposure_apply_physical_camera_exposure",), False)
    set_prop(settings, ("override_local_exposure_method",), False)
    set_prop(settings, ("override_local_exposure_detail_strength", "b_override_local_exposure_detail_strength"), False)
    log(f"Configured exposure on {label}")


def configure_spring_arm(comp) -> None:
    set_prop(comp, ("enable_camera_lag", "b_enable_camera_lag"), False)
    set_prop(comp, ("enable_camera_rotation_lag", "b_enable_camera_rotation_lag"), False)
    set_prop(comp, ("use_pawn_control_rotation", "bUsePawnControlRotation"), True)
    set_prop(comp, ("inherit_pitch", "bInheritPitch"), True)
    set_prop(comp, ("inherit_yaw", "bInheritYaw"), True)
    set_prop(comp, ("inherit_roll", "bInheritRoll"), False)
    set_prop(comp, ("target_arm_length", "TargetArmLength"), 0.0)
    set_prop(comp, ("socket_offset", "SocketOffset"), unreal.Vector(0.0, 0.0, 0.0))
    set_prop(comp, ("relative_rotation", "RelativeRotation"), unreal.Rotator(0.0, 0.0, 0.0))


def configure_camera(comp) -> None:
    settings = comp.post_process_settings
    configure_post_process_settings(settings, comp.get_name())
    comp.post_process_settings = settings
    set_prop(comp, ("post_process_blend_weight",), 1.0)
    set_prop(comp, ("use_pawn_control_rotation", "bUsePawnControlRotation"), True)
    set_prop(comp, ("use_controller_view_rotation", "bUseControllerViewRotation"), False)
    set_prop(comp, ("field_of_view", "FieldOfView"), 90.0)


def configure_blueprint_components(bp) -> None:
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    seen = set()
    for handle in sds.k2_gather_subobject_data_for_blueprint(bp):
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
        if not obj:
            continue
        oid = id(obj)
        if oid in seen:
            continue
        seen.add(oid)

        class_name = obj.get_class().get_name()
        if "SpringArmComponent" in class_name:
            configure_spring_arm(obj)
        elif "CameraComponent" in class_name and "FirstPersonCamera" in obj.get_name():
            configure_camera(obj)


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    bp = unreal.load_asset(BP_ASSET)
    if not bp:
        raise RuntimeError(f"Missing {BP_ASSET}")

    cdo = unreal.get_default_object(bp.generated_class())
    set_prop(cdo, ("BODYCAM",), True)
    set_prop(cdo, ("FOV_Base",), 90.0)

    for comp in cdo.get_components_by_class(unreal.ActorComponent.static_class()):
        if "CharacterMovementComponent" in comp.get_class().get_name():
            set_prop(comp, ("gravity_scale", "GravityScale"), 0.0)

    configure_blueprint_components(bp)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)
    log("Restored original FPS arm/weapon framing")


main()
