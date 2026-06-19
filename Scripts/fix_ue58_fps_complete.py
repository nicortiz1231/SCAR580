"""UE 5.8 FPS view parity: void background, vignette, visible arms/weapons."""

import unreal
from pathlib import Path

MAP_PATH = "/Game/BodycamFPSKIT/Maps/Map_Test"
BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
AC_BODY_CAM = "/Game/BodycamFPSKIT/Blueprints/Components/AC_BodycamCamera"
M_VIGNETTE = "/Game/BodycamFPSKIT/Blueprints/Camera/Materials/M_Vignette"
M_FISHEYE = "/Game/BodycamFPSKIT/Blueprints/Camera/Materials/M_FishEyeLens"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_ue58_fps_complete.log")

LIGHT_INTENSITY = {
    "AR_KeyLight": 6.0,
    "AR_FillLight": 4.0,
    "WeaponLight": 5.0,
    "DirectionalLight": 4.0,
    "FillLight_Back": 3.0,
    "FillLight_Top": 3.0,
}


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[fix_ue58_fps_complete] {msg}")


def obj_label(obj) -> str:
    try:
        return obj.get_name()
    except Exception:
        return type(obj).__name__


def set_prop(obj, names, value) -> bool:
    label = obj_label(obj)
    for name in names:
        try:
            obj.set_editor_property(name, value)
            log(f"Set {label}.{name} = {value}")
            return True
        except Exception as exc:
            log(f"Failed {name} on {label}: {exc}")
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
        none_method = getattr(unreal.LocalExposureMethod, "NONE", None)
        if none_method is not None:
            set_prop(settings, ("local_exposure_method",), none_method)
    except Exception as exc:
        log(f"Skipped local_exposure_method: {exc}")
    set_prop(settings, ("override_local_exposure_highlight_contrast_scale", "b_override_local_exposure_highlight_contrast_scale"), True)
    set_prop(settings, ("local_exposure_highlight_contrast_scale",), 1.0)
    set_prop(settings, ("override_local_exposure_shadow_contrast_scale", "b_override_local_exposure_shadow_contrast_scale"), True)
    set_prop(settings, ("local_exposure_shadow_contrast_scale",), 1.0)
    set_prop(settings, ("override_local_exposure_detail_strength", "b_override_local_exposure_detail_strength"), True)
    set_prop(settings, ("local_exposure_detail_strength",), 0.0)
    log(f"Configured manual exposure on {label}")


def fix_post_process_material(path: str) -> None:
    mat = unreal.load_asset(path)
    if not mat:
        log(f"Missing material {path}")
        return
    try:
        current = mat.get_editor_property("blend_mode")
    except Exception:
        return
    log(f"{path} blend_mode={current}")
    if current == unreal.BlendMode.BLEND_OPAQUE:
        mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
        log(f"Set {path} to BLEND_TRANSLUCENT")
    try:
        unreal.MaterialEditingLibrary.recompile_material(mat)
    except Exception as exc:
        log(f"Recompile skipped for {path}: {exc}")
    unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)


def configure_mesh_component(comp) -> None:
    # FPS arms/camera are spawned at runtime by the blueprint graph, not on the CDO.
    # Avoid touching CharacterMesh0 (third-person mannequin) defaults here.
    pass


def configure_light_component(comp) -> None:
    set_prop(comp, ("b_hidden_in_game", "hidden_in_game"), False)
    set_prop(comp, ("b_visible", "visible"), True)
    name = comp.get_name()
    intensity = 4.0
    for token, value in LIGHT_INTENSITY.items():
        if token in name:
            intensity = value
            break
    set_prop(comp, ("intensity", "Intensity"), intensity)


def configure_camera_component(comp) -> None:
    set_prop(comp, ("post_process_blend_weight",), 1.0)
    settings = comp.post_process_settings
    configure_post_process_settings(settings, comp.get_name())
    comp.post_process_settings = settings


def configure_actor_components(actor_like, label: str) -> None:
    if not hasattr(actor_like, "get_components_by_class"):
        log(f"{label}: no component iterator")
        return
    comps = actor_like.get_components_by_class(unreal.ActorComponent.static_class())
    log(f"{label}: {len(comps)} components")
    for comp in comps:
        class_name = comp.get_class().get_name()
        name = comp.get_name()
        log(f"  {name} ({class_name})")
        if "SkeletalMeshComponent" in class_name:
            configure_mesh_component(comp)
        if any(token in class_name for token in ("PointLightComponent", "SpotLightComponent", "DirectionalLightComponent")):
            configure_light_component(comp)
        if "CameraComponent" in class_name:
            configure_camera_component(comp)
        if "SpringArmComponent" in class_name:
            set_prop(comp, ("enable_camera_lag", "b_enable_camera_lag"), False)
            set_prop(comp, ("enable_camera_rotation_lag", "b_enable_camera_rotation_lag"), False)
        if "CharacterMovementComponent" in class_name:
            set_prop(comp, ("gravity_scale", "GravityScale"), 0.0)


def configure_character_blueprint() -> None:
    bp = unreal.load_asset(BP_ASSET)
    if not bp:
        raise RuntimeError(f"Missing {BP_ASSET}")

    cdo = unreal.get_default_object(bp.generated_class())
    set_prop(cdo, ("BODYCAM",), True)
    configure_actor_components(cdo, "BP_FPCharacter CDO")

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)


def configure_bodycam_component_blueprint() -> None:
    bp = unreal.load_asset(f"{AC_BODY_CAM}.{Path(AC_BODY_CAM).name}")
    if not bp:
        log("AC_BodycamCamera blueprint missing")
        return

    generated = bp.generated_class()
    cdo = unreal.get_default_object(generated)
    log(f"AC_BodycamCamera class={generated.get_name()}")

    # ActorComponent blueprints expose their template component as the CDO itself.
    if isinstance(cdo, unreal.ActorComponent):
        class_name = cdo.get_class().get_name()
        if "CameraComponent" in class_name:
            configure_camera_component(cdo)
        return

    configure_actor_components(cdo, "AC_BodycamCamera CDO")
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(AC_BODY_CAM, only_if_is_dirty=False)


def configure_map_post_process() -> None:
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not world:
        raise RuntimeError("Editor world unavailable")

    volume = None
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PostProcessVolume.static_class()):
        volume = actor
        break
    if not volume:
        raise RuntimeError("PostProcessVolume missing in Map_Test")

    set_prop(volume, ("unbound", "b_unbound"), True)
    configure_post_process_settings(volume.settings, volume.get_name())
    volume.settings = volume.settings


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    fix_post_process_material(M_VIGNETTE)
    fix_post_process_material(M_FISHEYE)
    configure_character_blueprint()
    configure_bodycam_component_blueprint()
    configure_map_post_process()
    unreal.EditorLoadingAndSavingUtils.save_map(unreal.load_asset(MAP_PATH), MAP_PATH)
    log("Finished UE 5.8 FPS complete fix")


main()
