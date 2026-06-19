"""Force SCAR-580 to match 5.7.4 black-background FPS rendering in UE 5.8."""

import unreal
from pathlib import Path

MAP_PATH = "/Game/BodycamFPSKIT/Maps/Map_Test"
BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
AC_BODY_CAM = "/Game/BodycamFPSKIT/Blueprints/Components/AC_BodycamCamera"
M_VIGNETTE = "/Game/BodycamFPSKIT/Blueprints/Camera/Materials/M_Vignette"
MPC_VIGNETTE = "/Game/BodycamFPSKIT/Blueprints/Camera/Materials/MPC_Vignette"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_ue58_rendering.log")


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[fix_ue58_rendering] {msg}")


def set_prop(obj, names, value) -> bool:
    label = getattr(obj, "get_class", lambda: type(obj))()
    label_name = label.get_name() if hasattr(label, "get_name") else type(obj).__name__
    for name in names:
        try:
            obj.set_editor_property(name, value)
            log(f"Set {label_name}.{name} = {value}")
            return True
        except Exception as exc:
            log(f"Failed {name}: {exc}")
    return False


def dump_exposure_props(settings, label: str) -> None:
    for name in sorted(dir(settings)):
        if any(key in name.lower() for key in ("exposure", "vignette", "brightness", "ev100")):
            try:
                value = settings.get_editor_property(name)
                log(f"{label}.{name} = {value}")
            except Exception:
                pass


def configure_post_process_settings(settings) -> None:
    dump_exposure_props(settings, "before")

    set_prop(settings, ("override_auto_exposure_method",), True)
    set_prop(settings, ("auto_exposure_method",), unreal.AutoExposureMethod.AEM_MANUAL)
    set_prop(settings, ("override_auto_exposure_bias",), True)
    set_prop(settings, ("auto_exposure_bias",), 0.0)

    # UE 5.1+ EV100 names
    set_prop(settings, ("override_auto_exposure_min_ev100", "b_override_auto_exposure_min_ev100"), True)
    set_prop(settings, ("auto_exposure_min_ev100",), 0.0)
    set_prop(settings, ("override_auto_exposure_max_ev100", "b_override_auto_exposure_max_ev100"), True)
    set_prop(settings, ("auto_exposure_max_ev100",), 0.0)

    # Legacy brightness names still used by this project's volume in 5.7
    set_prop(settings, ("override_auto_exposure_min_brightness", "b_override_auto_exposure_min_brightness"), True)
    set_prop(settings, ("auto_exposure_min_brightness",), 1.0)
    set_prop(settings, ("override_auto_exposure_max_brightness", "b_override_auto_exposure_max_brightness"), True)
    set_prop(settings, ("auto_exposure_max_brightness",), 1.0)

    set_prop(settings, ("override_vignette_intensity", "b_override_vignette_intensity"), True)
    set_prop(settings, ("vignette_intensity",), 0.4)

    # UE 5.8 local exposure can blow out empty scenes to white in PIE.
    set_prop(settings, ("override_local_exposure_method",), True)
    try:
        set_prop(settings, ("local_exposure_method",), unreal.LocalExposureMethod.NONE)
    except Exception:
        pass
    set_prop(settings, ("override_local_exposure_highlight_contrast_scale",), True)
    set_prop(settings, ("local_exposure_highlight_contrast_scale",), 1.0)
    set_prop(settings, ("override_local_exposure_shadow_contrast_scale",), True)
    set_prop(settings, ("local_exposure_shadow_contrast_scale",), 1.0)
    set_prop(settings, ("override_local_exposure_detail_strength",), True)
    set_prop(settings, ("local_exposure_detail_strength",), 0.0)

    set_prop(settings, ("b_override_eye_adaptation_min_brightness",), True)
    set_prop(settings, ("eye_adaptation_min_brightness",), 1.0)
    set_prop(settings, ("b_override_eye_adaptation_max_brightness",), True)
    set_prop(settings, ("eye_adaptation_max_brightness",), 1.0)
    set_prop(settings, ("b_override_exposure_offset",), True)
    set_prop(settings, ("exposure_offset",), 0.0)

    dump_exposure_props(settings, "after")


def configure_map_post_process_volume() -> None:
    editor_subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = editor_subsystem.get_editor_world()
    if not world:
        raise RuntimeError("Editor world unavailable")

    volumes = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PostProcessVolume.static_class())
    if not volumes:
        raise RuntimeError("No PostProcessVolume found in Map_Test")

    for volume in volumes:
        set_prop(volume, ("unbound", "b_unbound"), True)
        settings = volume.settings
        configure_post_process_settings(settings)
        volume.settings = settings
        log(f"Configured map volume {volume.get_name()}")


def configure_blueprint_camera_post_process(bp) -> None:
    try:
        scs = bp.simple_construction_script
    except Exception as exc:
        log(f"Could not read simple construction script: {exc}")
        scs = None

    if scs:
        try:
            nodes = scs.get_all_nodes()
        except Exception as exc:
            log(f"Could not enumerate SCS nodes: {exc}")
            nodes = []
        for node in nodes:
            try:
                comp = node.component_template
                if not comp:
                    continue
                class_name = comp.get_class().get_name()
                name = str(node.get_variable_name())
                if "CameraComponent" in class_name:
                    settings = comp.post_process_settings
                    configure_post_process_settings(settings)
                    comp.post_process_settings = settings
                    set_prop(comp, ("post_process_blend_weight",), 1.0)
                    log(f"Configured camera component template {name}")
                if any(token in class_name for token in ("PointLightComponent", "SpotLightComponent", "DirectionalLightComponent")):
                    set_prop(comp, ("visible", "b_visible"), True)
                    set_prop(comp, ("hidden_in_game", "b_hidden_in_game"), False)
                    intensity = 3.0
                    if "Fill" in name:
                        intensity = 2.0
                    if "Key" in name or "Directional" in name:
                        intensity = 4.0
                    if "Weapon" in name:
                        intensity = 3.0
                    set_prop(comp, ("intensity", "Intensity"), intensity)
                    log(f"Configured light component template {name}")
            except Exception as exc:
                log(f"SCS node failed: {exc}")


def configure_character_lights(bp) -> None:
    cdo = unreal.get_default_object(bp.generated_class())
    set_prop(cdo, ("BODYCAM",), True)

    light_names = {
        "AR_KeyLight": 4.0,
        "AR_FillLight": 2.0,
        "WeaponLight": 3.0,
        "DirectionalLight": 3.0,
    }

    for comp in cdo.get_components_by_class(unreal.ActorComponent.static_class()):
        class_name = comp.get_class().get_name()
        name = comp.get_name()
        if "CharacterMovementComponent" in class_name:
            set_prop(comp, ("gravity_scale", "GravityScale"), 0.0)
        if "SpringArmComponent" in class_name:
            set_prop(comp, ("enable_camera_lag", "b_enable_camera_lag"), False)
            set_prop(comp, ("enable_camera_rotation_lag", "b_enable_camera_rotation_lag"), False)
        if any(token in class_name for token in ("PointLightComponent", "SpotLightComponent", "DirectionalLightComponent")):
            set_prop(comp, ("visible", "b_visible"), True)
            set_prop(comp, ("hidden_in_game", "b_hidden_in_game"), False)
            for light_name, intensity in light_names.items():
                if light_name in name:
                    set_prop(comp, ("intensity", "Intensity"), intensity)

    for comp_name, intensity in light_names.items():
        try:
            comp = unreal.BlueprintEditorLibrary.get_component_template(bp, comp_name)
        except Exception:
            comp = None
        if not comp:
            continue
        set_prop(comp, ("visible", "b_visible"), True)
        set_prop(comp, ("hidden_in_game", "b_hidden_in_game"), False)
        set_prop(comp, ("intensity", "Intensity"), intensity)
        log(f"Configured blueprint light template {comp_name}")


def recompile_material(path: str) -> None:
    asset = unreal.load_asset(path)
    if not asset:
        log(f"Missing material asset {path}")
        return
    try:
        unreal.MaterialEditingLibrary.recompile_material(asset)
        unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
        log(f"Recompiled material {path}")
    except Exception as exc:
        log(f"Failed to recompile {path}: {exc}")


def compile_and_save(path: str) -> None:
    asset = unreal.load_asset(path)
    if not asset:
        log(f"Missing asset {path}")
        return
    unreal.BlueprintEditorLibrary.compile_blueprint(asset)
    unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
    log(f"Compiled and saved {path}")


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)

    recompile_material(M_VIGNETTE)
    recompile_material(MPC_VIGNETTE)

    bp = unreal.load_asset(BP_ASSET)
    if not bp:
        raise RuntimeError(f"Failed to load {BP_ASSET}")

    configure_character_lights(bp)
    configure_blueprint_camera_post_process(bp)
    compile_and_save(BP_PATH)
    compile_and_save(AC_BODY_CAM)

    configure_map_post_process_volume()
    unreal.EditorLoadingAndSavingUtils.save_map(unreal.load_asset(MAP_PATH), MAP_PATH)
    log("Finished UE 5.8 rendering parity fix")


main()
