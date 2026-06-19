"""Restore UE 5.8 FPS view parity with working SCAR 5.7 project."""

import unreal
from pathlib import Path

MAP_PATH = "/Game/BodycamFPSKIT/Maps/Map_Test"
BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
M_VIGNETTE = "/Game/BodycamFPSKIT/Blueprints/Camera/Materials/M_Vignette"
M_FISHEYE = "/Game/BodycamFPSKIT/Blueprints/Camera/Materials/M_FishEyeLens"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_ue58_final.log")


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[fix_ue58_final] {msg}")


def set_prop(obj, names, value) -> bool:
    label = obj.get_name() if hasattr(obj, "get_name") else type(obj).__name__
    for name in names:
        try:
            obj.set_editor_property(name, value)
            log(f"Set {label}.{name} = {value}")
            return True
        except Exception as exc:
            log(f"Failed {label}.{name}: {exc}")
    return False


def configure_post_process_settings(settings, label: str) -> None:
    # Lock exposure the same way Map_Test does in 5.7, using properties UE 5.8 still honors.
    set_prop(settings, ("override_auto_exposure_method", "b_override_auto_exposure_method"), True)
    set_prop(settings, ("auto_exposure_method",), unreal.AutoExposureMethod.AEM_MANUAL)
    set_prop(settings, ("override_auto_exposure_bias", "b_override_auto_exposure_bias"), True)
    set_prop(settings, ("auto_exposure_bias",), 0.0)
    set_prop(settings, ("override_auto_exposure_min_brightness", "b_override_auto_exposure_min_brightness"), True)
    set_prop(settings, ("auto_exposure_min_brightness",), 1.0)
    set_prop(settings, ("override_auto_exposure_max_brightness", "b_override_auto_exposure_max_brightness"), True)
    set_prop(settings, ("auto_exposure_max_brightness",), 1.0)

    # UE 5.8: physical camera exposure blows empty scenes to white if left enabled.
    set_prop(settings, ("override_auto_exposure_apply_physical_camera_exposure",), True)
    set_prop(settings, ("auto_exposure_apply_physical_camera_exposure",), False)

    set_prop(settings, ("override_local_exposure_detail_strength", "b_override_local_exposure_detail_strength"), True)
    set_prop(settings, ("local_exposure_detail_strength",), 0.0)
    set_prop(settings, ("override_local_exposure_highlight_contrast_scale", "b_override_local_exposure_highlight_contrast_scale"), True)
    set_prop(settings, ("local_exposure_highlight_contrast_scale",), 1.0)
    set_prop(settings, ("override_local_exposure_shadow_contrast_scale", "b_override_local_exposure_shadow_contrast_scale"), True)
    set_prop(settings, ("local_exposure_shadow_contrast_scale",), 1.0)
    log(f"Configured post process on {label}")


def fix_post_process_material(path: str) -> None:
    mat = unreal.load_asset(path)
    if not mat:
        log(f"Missing {path}")
        return
    blend = mat.get_editor_property("blend_mode")
    log(f"{path} blend_mode={blend}")
    # UE 5.8 renders opaque bodycam PP mats as a solid white plate unless translucent.
    if blend == unreal.BlendMode.BLEND_OPAQUE:
        mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
        log(f"Set {path} to BLEND_TRANSLUCENT for UE 5.8")
        unreal.MaterialEditingLibrary.recompile_material(mat)
        unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)


def configure_character() -> None:
    bp = unreal.load_asset(BP_ASSET)
    if not bp:
        raise RuntimeError(f"Missing {BP_ASSET}")
    cdo = unreal.get_default_object(bp.generated_class())
    set_prop(cdo, ("BODYCAM",), True)
    for comp in cdo.get_components_by_class(unreal.ActorComponent.static_class()):
        class_name = comp.get_class().get_name()
        if "CharacterMovementComponent" in class_name:
            set_prop(comp, ("gravity_scale", "GravityScale"), 0.0)
        if "SpringArmComponent" in class_name:
            set_prop(comp, ("enable_camera_lag", "b_enable_camera_lag"), False)
            set_prop(comp, ("enable_camera_rotation_lag", "b_enable_camera_rotation_lag"), False)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)


def configure_map() -> None:
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not world:
        raise RuntimeError("No editor world")

    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PostProcessVolume.static_class()):
        set_prop(actor, ("unbound", "b_unbound"), True)
        configure_post_process_settings(actor.settings, actor.get_name())
        actor.settings = actor.settings
        log(f"Updated {actor.get_name()}")


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    fix_post_process_material(M_VIGNETTE)
    fix_post_process_material(M_FISHEYE)
    configure_character()
    configure_map()
    unreal.EditorLoadingAndSavingUtils.save_map(unreal.load_asset(MAP_PATH), MAP_PATH)
    log("Done")


main()
