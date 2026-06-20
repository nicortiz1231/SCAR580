"""Make FPS arms/weapons visible in Map_AR PIE on Mac while keeping iOS AR setup."""

import unreal
from pathlib import Path

MAP_AR = "/Game/SCAR580/Maps/Map_AR"
GM_AR = "/Game/SCAR580/Blueprints/GameModes/GM_SCAR_AR"
BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
M_VIGNETTE = "/Game/BodycamFPSKIT/Blueprints/Camera/Materials/M_Vignette"
M_FISHEYE = "/Game/BodycamFPSKIT/Blueprints/Camera/Materials/M_FishEyeLens"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_ar_pie_preview.log")

LIGHT_INTENSITY = {
    "AR_KeyLight": 6.0,
    "AR_FillLight": 4.0,
    "AR_Left": 3.0,
    "AR_Right": 3.0,
    "WeaponLight": 5.0,
    "FillLight_Back": 3.0,
    "FillLight_Top": 3.0,
}


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[fix_ar_pie_preview] {msg}")


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
    set_prop(settings, ("auto_exposure_bias",), 0.0)
    set_prop(settings, ("override_auto_exposure_min_brightness", "b_override_auto_exposure_min_brightness"), True)
    set_prop(settings, ("auto_exposure_min_brightness",), 1.0)
    set_prop(settings, ("override_auto_exposure_max_brightness", "b_override_auto_exposure_max_brightness"), True)
    set_prop(settings, ("auto_exposure_max_brightness",), 1.0)
    set_prop(settings, ("override_auto_exposure_apply_physical_camera_exposure",), True)
    set_prop(settings, ("auto_exposure_apply_physical_camera_exposure",), False)
    set_prop(settings, ("b_override_eye_adaptation_min_brightness",), True)
    set_prop(settings, ("eye_adaptation_min_brightness",), 1.0)
    set_prop(settings, ("b_override_eye_adaptation_max_brightness",), True)
    set_prop(settings, ("eye_adaptation_max_brightness",), 1.0)
    set_prop(settings, ("override_local_exposure_method", "b_override_local_exposure_method"), True)
    try:
        set_prop(settings, ("local_exposure_method",), unreal.LocalExposureMethod.NONE)
    except Exception:
        pass
    set_prop(settings, ("override_local_exposure_detail_strength", "b_override_local_exposure_detail_strength"), True)
    set_prop(settings, ("local_exposure_detail_strength",), 0.0)
    log(f"Configured exposure on {label}")


def fix_post_process_material(path: str) -> None:
    mat = unreal.load_asset(path)
    if not mat:
        log(f"Missing material {path}")
        return
    try:
        current = mat.get_editor_property("blend_mode")
    except Exception:
        return
    if current == unreal.BlendMode.BLEND_OPAQUE:
        mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
        log(f"Set {path} to BLEND_TRANSLUCENT")
    try:
        unreal.MaterialEditingLibrary.recompile_material(mat)
    except Exception as exc:
        log(f"Recompile skipped for {path}: {exc}")
    unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)


def configure_light_component(comp) -> None:
    set_prop(comp, ("hidden_in_game", "b_hidden_in_game"), False)
    set_prop(comp, ("visible", "b_visible"), True)
    intensity = 4.0
    for token, value in LIGHT_INTENSITY.items():
        if token in comp.get_name():
            intensity = value
            break
    set_prop(comp, ("intensity", "Intensity"), intensity)


def configure_camera_component(comp) -> None:
    settings = comp.post_process_settings
    configure_post_process_settings(settings, comp.get_name())
    comp.post_process_settings = settings
    set_prop(comp, ("post_process_blend_weight",), 1.0)


def configure_blueprint_components(bp) -> None:
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = sds.k2_gather_subobject_data_for_blueprint(bp)
    seen = set()

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
            configure_camera_component(obj)
        if any(token in class_name for token in ("PointLightComponent", "SpotLightComponent", "DirectionalLightComponent")):
            configure_light_component(obj)

    cdo = unreal.get_default_object(bp.generated_class())
    set_prop(cdo, ("BODYCAM",), True)
    for comp in cdo.get_components_by_class(unreal.ActorComponent.static_class()):
        class_name = comp.get_class().get_name()
        if "CharacterMovementComponent" in class_name:
            set_prop(comp, ("gravity_scale", "GravityScale"), 0.0)
        if "SpringArmComponent" in class_name:
            set_prop(comp, ("enable_camera_lag", "b_enable_camera_lag"), False)
            set_prop(comp, ("enable_camera_rotation_lag", "b_enable_camera_rotation_lag"), False)


def show_actor(actor) -> None:
    actor.set_actor_hidden_in_game(False)
    actor.set_is_temporarily_hidden_in_editor(False)


def ensure_post_process_volume(world) -> None:
    editor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    volume = None
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PostProcessVolume.static_class()):
        volume = actor
        break

    if not volume:
        volume = editor_subsystem.spawn_actor_from_class(
            unreal.PostProcessVolume,
            unreal.Vector(0, 0, 0),
            unreal.Rotator(0, 0, 0),
        )
        volume.set_actor_label("AR_PostProcessVolume")
        log("Spawned PostProcessVolume for Map_AR")

    set_prop(volume, ("unbound", "b_unbound"), True)
    configure_post_process_settings(volume.settings, volume.get_name())
    volume.settings = volume.settings


def configure_map_ar() -> None:
    unreal.EditorLoadingAndSavingUtils.load_map(MAP_AR)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not world:
        raise RuntimeError("Editor world unavailable")

    gm_class = unreal.load_class(None, f"{GM_AR}.GM_SCAR_AR_C")
    world.get_world_settings().set_editor_property("default_game_mode", gm_class)
    log("Set world default_game_mode to GM_SCAR_AR")

    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor.static_class()):
        cls = actor.get_class().get_name()
        if cls in {"DirectionalLight", "SkyLight"}:
            show_actor(actor)
            log(f"Unhid {actor.get_name()} for Mac PIE preview")
        if cls in {"DocumentationActor", "TextRenderActor", "ExponentialHeightFog"}:
            actor.set_actor_hidden_in_game(True)
            actor.set_is_temporarily_hidden_in_editor(True)

    ensure_post_process_volume(world)
    unreal.EditorLoadingAndSavingUtils.save_current_level()
    log("Saved Map_AR")


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    fix_post_process_material(M_VIGNETTE)
    fix_post_process_material(M_FISHEYE)

    bp = unreal.load_asset(BP_ASSET)
    if not bp:
        raise RuntimeError(f"Missing {BP_ASSET}")
    configure_blueprint_components(bp)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)
    log("Updated BP_FPCharacter camera/lighting defaults")

    configure_map_ar()
    log("Done - press Play on Map_AR to verify arms/weapons are visible")


main()
