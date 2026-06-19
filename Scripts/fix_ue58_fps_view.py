"""Minimal UE 5.8 fix: exposure lock + translucent vignette material."""

import unreal
from pathlib import Path

MAP_PATH = "/Game/BodycamFPSKIT/Maps/Map_Test"
BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
M_VIGNETTE = "/Game/BodycamFPSKIT/Blueprints/Camera/Materials/M_Vignette"
M_FISHEYE = "/Game/BodycamFPSKIT/Blueprints/Camera/Materials/M_FishEyeLens"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_ue58_fps_view.log")


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[fix_ue58_fps_view] {msg}")


def set_prop(obj, names, value) -> bool:
    for name in names:
        try:
            obj.set_editor_property(name, value)
            log(f"Set {name} = {value}")
            return True
        except Exception as exc:
            log(f"Failed {name}: {exc}")
    return False


def configure_post_process_settings(settings, label: str) -> None:
    set_prop(settings, ("override_auto_exposure_method", "b_override_auto_exposure_method"), True)
    set_prop(settings, ("auto_exposure_method",), unreal.AutoExposureMethod.AEM_MANUAL)
    set_prop(settings, ("override_auto_exposure_bias", "b_override_auto_exposure_bias"), True)
    set_prop(settings, ("auto_exposure_bias",), 0.0)
    set_prop(settings, ("override_auto_exposure_min_brightness", "b_override_auto_exposure_min_brightness"), True)
    set_prop(settings, ("auto_exposure_min_brightness",), 1.0)
    set_prop(settings, ("override_auto_exposure_max_brightness", "b_override_auto_exposure_max_brightness"), True)
    set_prop(settings, ("auto_exposure_max_brightness",), 1.0)
    set_prop(settings, ("b_override_eye_adaptation_min_brightness",), True)
    set_prop(settings, ("eye_adaptation_min_brightness",), 1.0)
    set_prop(settings, ("b_override_eye_adaptation_max_brightness",), True)
    set_prop(settings, ("eye_adaptation_max_brightness",), 1.0)
    set_prop(settings, ("override_local_exposure_method", "b_override_local_exposure_method"), True)
    try:
        set_prop(settings, ("local_exposure_method",), unreal.LocalExposureMethod.NONE)
    except Exception:
        pass
    set_prop(settings, ("override_local_exposure_highlight_contrast_scale", "b_override_local_exposure_highlight_contrast_scale"), True)
    set_prop(settings, ("local_exposure_highlight_contrast_scale",), 1.0)
    set_prop(settings, ("override_local_exposure_shadow_contrast_scale", "b_override_local_exposure_shadow_contrast_scale"), True)
    set_prop(settings, ("local_exposure_shadow_contrast_scale",), 1.0)
    set_prop(settings, ("override_local_exposure_detail_strength", "b_override_local_exposure_detail_strength"), True)
    set_prop(settings, ("local_exposure_detail_strength",), 0.0)
    log(f"Configured exposure lock on {label}")


def fix_post_process_material(path: str) -> None:
    mat = unreal.load_asset(path)
    if not mat:
        log(f"Missing material {path}")
        return

    try:
        current = mat.get_editor_property("blend_mode")
    except Exception:
        log(f"{path} has no blend_mode property")
        return

    log(f"{path} blend before: {current}")
    if current == unreal.BlendMode.BLEND_OPAQUE:
        mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
        log(f"Set {path} blend_mode to BLEND_TRANSLUCENT")

    try:
        unreal.MaterialEditingLibrary.recompile_material(mat)
    except Exception as exc:
        log(f"Recompile skipped for {path}: {exc}")

    unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
    log(f"{path} blend after: {mat.get_editor_property('blend_mode')}")


def fix_vignette_material() -> None:
    fix_post_process_material(M_VIGNETTE)
    fix_post_process_material(M_FISHEYE)


def configure_character_defaults() -> None:
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


def configure_map_post_process() -> None:
    editor_subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = editor_subsystem.get_editor_world()
    if not world:
        raise RuntimeError("Editor world unavailable")

    volume = None
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PostProcessVolume.static_class()):
        volume = actor
        break
    if not volume:
        raise RuntimeError("PostProcessVolume missing in Map_Test")

    set_prop(volume, ("unbound", "b_unbound"), True)
    configure_post_process_settings(volume.settings, "PostProcessVolume_0")
    volume.settings = volume.settings


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    fix_vignette_material()
    configure_character_defaults()
    configure_map_post_process()
    unreal.EditorLoadingAndSavingUtils.save_map(unreal.load_asset(MAP_PATH), MAP_PATH)
    log("Finished UE 5.8 FPS view fix")


main()
