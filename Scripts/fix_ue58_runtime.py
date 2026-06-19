"""UE 5.8 runtime bodycam fix: BeginSetup reapplies PP every spawn, so patch materials + PPV + camera."""

import unreal
from pathlib import Path

MAP_PATH = "/Game/BodycamFPSKIT/Maps/Map_Test"
BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
M_OUTLINE = "/Game/BodycamFPSKIT/Blueprints/Materials/M_Outline"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_ue58_runtime.log")

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
    text = LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n"
    LOG_PATH.write_text(text)
    unreal.log(f"[fix_ue58_runtime] {msg}")


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
    set_prop(settings, ("override_local_exposure_method",), False)
    set_prop(settings, ("override_local_exposure_detail_strength", "b_override_local_exposure_detail_strength"), False)
    log(f"Configured post process on {label}")


def make_outline_passthrough() -> None:
    """M_Outline uses CustomDepth; in UE 5.8 opaque PP with empty CustomDepth = white center."""
    mat = unreal.load_asset(M_OUTLINE)
    if not mat:
        raise RuntimeError(f"Missing {M_OUTLINE}")

    log(f"{M_OUTLINE} blend before={mat.get_editor_property('blend_mode')}")
    unreal.MaterialEditingLibrary.delete_all_material_expressions(mat)

    scene_tex = unreal.MaterialEditingLibrary.create_material_expression(
        mat,
        unreal.MaterialExpressionSceneTexture,
        -200,
        0,
    )
    scene_tex.set_editor_property("scene_texture_id", unreal.SceneTextureId.PPI_POST_PROCESS_INPUT0)
    unreal.MaterialEditingLibrary.connect_material_property(
        scene_tex,
        "",
        unreal.MaterialProperty.MP_EMISSIVE_COLOR,
    )

    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property("material_domain", unreal.MaterialDomain.MD_POST_PROCESS)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(M_OUTLINE, only_if_is_dirty=False)
    log(f"{M_OUTLINE} rebuilt as scene passthrough, blend={mat.get_editor_property('blend_mode')}")


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
            settings = obj.post_process_settings
            log(
                f"{obj.get_name()} before: method={settings.get_editor_property('auto_exposure_method')} "
                f"apply_physical={settings.get_editor_property('auto_exposure_apply_physical_camera_exposure')}"
            )
            configure_post_process_settings(settings, obj.get_name())
            obj.post_process_settings = settings
            set_prop(obj, ("post_process_blend_weight",), 1.0)
        if any(token in class_name for token in ("PointLightComponent", "SpotLightComponent", "DirectionalLightComponent")):
            set_prop(obj, ("hidden_in_game", "b_hidden_in_game"), False)
            set_prop(obj, ("visible", "b_visible"), True)
            intensity = 4.0
            for token, value in LIGHT_INTENSITY.items():
                if token in obj.get_name():
                    intensity = value
                    break
            set_prop(obj, ("intensity", "Intensity"), intensity)

    cdo = unreal.get_default_object(bp.generated_class())
    set_prop(cdo, ("BODYCAM",), True)
    for comp in cdo.get_components_by_class(unreal.ActorComponent.static_class()):
        class_name = comp.get_class().get_name()
        if "CharacterMovementComponent" in class_name:
            set_prop(comp, ("gravity_scale", "GravityScale"), 0.0)
        if "SpringArmComponent" in class_name:
            set_prop(comp, ("enable_camera_lag", "b_enable_camera_lag"), False)
            set_prop(comp, ("enable_camera_rotation_lag", "b_enable_camera_rotation_lag"), False)


def configure_map_post_process() -> None:
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not world:
        raise RuntimeError("Editor world unavailable")

    for volume in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PostProcessVolume.static_class()):
        set_prop(volume, ("unbound", "b_unbound"), True)
        settings = volume.settings
        configure_post_process_settings(settings, volume.get_name())
        volume.settings = settings
        log(f"Updated {volume.get_name()}")


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    make_outline_passthrough()

    bp = unreal.load_asset(BP_ASSET)
    if not bp:
        raise RuntimeError(f"Missing {BP_ASSET}")

    configure_blueprint_components(bp)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)

    configure_map_post_process()
    unreal.EditorLoadingAndSavingUtils.save_map(unreal.load_asset(MAP_PATH), MAP_PATH)
    log("Done")


main()
