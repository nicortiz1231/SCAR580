"""Apply exact 5.7.4 GitHub lighting + minimal UE 5.8 exposure fix (no PreExposure darkening)."""

import unreal
from pathlib import Path

MAP_PATH = "/Game/BodycamFPSKIT/Maps/Map_Test"
BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
M_OUTLINE = "/Game/BodycamFPSKIT/Blueprints/Materials/M_Outline"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_ue58_match_57.log")


def log(msg: str) -> None:
    text = LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n"
    LOG_PATH.write_text(text)
    unreal.log(f"[fix_ue58_match_57] {msg}")


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


def apply_ue58_exposure_fix(settings, label: str) -> None:
    """GitHub 5.7 uses bias=1.0 and BeginSetup AR lights (85 key). UE 5.8 needs apply_physical off + locked min/max."""
    set_prop(settings, ("override_auto_exposure_apply_physical_camera_exposure",), True)
    set_prop(settings, ("auto_exposure_apply_physical_camera_exposure",), False)
    set_prop(settings, ("override_auto_exposure_method", "b_override_auto_exposure_method"), True)
    set_prop(settings, ("auto_exposure_method",), unreal.AutoExposureMethod.AEM_MANUAL)
    set_prop(settings, ("override_auto_exposure_bias", "b_override_auto_exposure_bias"), True)
    set_prop(settings, ("auto_exposure_bias",), 1.0)
    set_prop(settings, ("override_auto_exposure_min_brightness", "b_override_auto_exposure_min_brightness"), True)
    set_prop(settings, ("auto_exposure_min_brightness",), 1.0)
    set_prop(settings, ("override_auto_exposure_max_brightness", "b_override_auto_exposure_max_brightness"), True)
    set_prop(settings, ("auto_exposure_max_brightness",), 1.0)
    log(f"UE58 exposure fix on {label}")


def make_outline_passthrough() -> None:
    mat = unreal.load_asset(M_OUTLINE)
    if not mat:
        raise RuntimeError(f"Missing {M_OUTLINE}")
    unreal.MaterialEditingLibrary.delete_all_material_expressions(mat)
    scene_tex = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionSceneTexture, -200, 0
    )
    scene_tex.set_editor_property("scene_texture_id", unreal.SceneTextureId.PPI_POST_PROCESS_INPUT0)
    unreal.MaterialEditingLibrary.connect_material_property(
        scene_tex, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR
    )
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property("material_domain", unreal.MaterialDomain.MD_POST_PROCESS)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(M_OUTLINE, only_if_is_dirty=False)
    log("M_Outline passthrough saved")


def configure_blueprint(bp) -> None:
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

        if "FirstPersonCamera" in obj.get_name():
            settings = obj.post_process_settings
            apply_ue58_exposure_fix(settings, obj.get_name())
            obj.post_process_settings = settings
            set_prop(obj, ("post_process_blend_weight",), 1.0)

        if "Light" in obj.get_class().get_name():
            set_prop(obj, ("hidden_in_game", "b_hidden_in_game"), False)
            set_prop(obj, ("visible", "b_visible"), True)

    set_prop(unreal.get_default_object(bp.generated_class()), ("BODYCAM",), True)


def configure_map() -> None:
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not world:
        raise RuntimeError("Editor world unavailable")

    for volume in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PostProcessVolume.static_class()):
        set_prop(volume, ("unbound", "b_unbound"), True)
        settings = volume.settings
        log(
            f"PPV before min={settings.get_editor_property('auto_exposure_min_brightness')} "
            f"max={settings.get_editor_property('auto_exposure_max_brightness')} "
            f"vignette={settings.get_editor_property('vignette_intensity')}"
        )
        apply_ue58_exposure_fix(settings, volume.get_name())
        volume.settings = settings
        log(
            f"PPV after min={settings.get_editor_property('auto_exposure_min_brightness')} "
            f"max={settings.get_editor_property('auto_exposure_max_brightness')}"
        )


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    make_outline_passthrough()

    bp = unreal.load_asset(BP_ASSET)
    if not bp:
        raise RuntimeError(f"Missing {BP_ASSET}")

    configure_blueprint(bp)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)
    configure_map()
    unreal.EditorLoadingAndSavingUtils.save_map(unreal.load_asset(MAP_PATH), MAP_PATH)
    log("Done")


main()
