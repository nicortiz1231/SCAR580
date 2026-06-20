"""Restore Map_AR FPS view to match Map_Test reference (weapon + centered arms)."""

import unreal
from pathlib import Path

MAP_AR = "/Game/SCAR580/Maps/Map_AR"
GM_AR = "/Game/SCAR580/Blueprints/GameModes/GM_SCAR_AR"
GM_FP = "/Game/BodycamFPSKIT/Blueprints/GameModes/GM_FP"
BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
AR_SESSION = "/Game/HandheldAR/D_ARSessionConfig"
M_VIGNETTE = "/Game/BodycamFPSKIT/Blueprints/Camera/Materials/M_Vignette"
M_FISHEYE = "/Game/BodycamFPSKIT/Blueprints/Camera/Materials/M_FishEyeLens"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_ar_fps_view.log")

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
    unreal.log(f"[fix_ar_fps_view] {msg}")


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
    # Match fix_ue58_lighting reference framing on black background.
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


def fix_post_process_material(path: str) -> None:
    mat = unreal.load_asset(path)
    if not mat:
        return
    try:
        if mat.get_editor_property("blend_mode") == unreal.BlendMode.BLEND_OPAQUE:
            mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
            log(f"Set {path} blend to translucent")
            unreal.MaterialEditingLibrary.recompile_material(mat)
            unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
    except Exception as exc:
        log(f"Skip material {path}: {exc}")


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
    set_prop(comp, ("use_pawn_control_rotation", "bUsePawnControlRotation"), True)
    set_prop(comp, ("use_controller_view_rotation", "bUseControllerViewRotation"), False)


def configure_spring_arm(comp) -> None:
    set_prop(comp, ("enable_camera_lag", "b_enable_camera_lag"), False)
    set_prop(comp, ("enable_camera_rotation_lag", "b_enable_camera_rotation_lag"), False)
    set_prop(comp, ("use_pawn_control_rotation", "bUsePawnControlRotation"), True)
    set_prop(comp, ("inherit_pitch", "bInheritPitch"), True)
    set_prop(comp, ("inherit_yaw", "bInheritYaw"), True)
    set_prop(comp, ("inherit_roll", "bInheritRoll"), False)


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
        elif "SpringArmComponent" in class_name:
            configure_spring_arm(obj)
        elif any(token in class_name for token in ("PointLightComponent", "SpotLightComponent")):
            configure_light_component(obj)

    cdo = unreal.get_default_object(bp.generated_class())
    set_prop(cdo, ("BODYCAM",), True)
    for comp in cdo.get_components_by_class(unreal.ActorComponent.static_class()):
        class_name = comp.get_class().get_name()
        if "CharacterMovementComponent" in class_name:
            set_prop(comp, ("gravity_scale", "GravityScale"), 0.0)


def configure_game_mode() -> None:
    gm = unreal.load_asset(f"{GM_AR}.GM_SCAR_AR")
    gm_fp = unreal.load_asset(f"{GM_FP}.GM_FP")
    if not gm or not gm_fp:
        raise RuntimeError("Missing GM_SCAR_AR or GM_FP")

    gm_cdo = unreal.get_default_object(gm.generated_class())
    fp_cdo = unreal.get_default_object(gm_fp.generated_class())

    # Use the same controller/HUD stack as the working FPS game mode.
    set_prop(gm_cdo, ("player_controller_class", "PlayerControllerClass"), fp_cdo.get_editor_property("player_controller_class"))
    set_prop(gm_cdo, ("hud_class", "HUDClass"), fp_cdo.get_editor_property("hud_class"))
    set_prop(gm_cdo, ("default_pawn_class", "DefaultPawnClass"), fp_cdo.get_editor_property("default_pawn_class"))

    unreal.BlueprintEditorLibrary.compile_blueprint(gm)
    unreal.EditorAssetLibrary.save_asset(GM_AR, only_if_is_dirty=False)
    log("GM_SCAR_AR now mirrors GM_FP pawn/controller/HUD")


def configure_ar_session() -> None:
    config = unreal.load_asset(AR_SESSION)
    if not config:
        raise RuntimeError(f"Missing {AR_SESSION}")

    # Keep camera passthrough on device, but do not hijack pawn camera with AR tracking.
    set_prop(config, ("bEnableAutomaticCameraOverlay",), True)
    set_prop(config, ("bEnableAutomaticCameraTracking",), False)
    unreal.EditorAssetLibrary.save_asset(AR_SESSION, only_if_is_dirty=False)
    log("Disabled AR automatic camera tracking (FPS camera stays on character)")


def configure_map_ar() -> None:
    unreal.EditorLoadingAndSavingUtils.load_map(MAP_AR)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not world:
        raise RuntimeError("Editor world unavailable")

    gm_class = unreal.load_class(None, f"{GM_AR}.GM_SCAR_AR_C")
    world.get_world_settings().set_editor_property("default_game_mode", gm_class)

    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PostProcessVolume.static_class()):
        set_prop(actor, ("unbound", "b_unbound"), True)
        configure_post_process_settings(actor.settings, actor.get_name())
        actor.settings = actor.settings

    unreal.EditorLoadingAndSavingUtils.save_current_level()
    log("Updated Map_AR post process + saved")


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

    configure_game_mode()
    configure_ar_session()
    configure_map_ar()
    log("Done - Play Map_AR; arms/weapon should match Map_Test reference")


main()
