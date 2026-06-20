"""Build SCAR-580 iOS AR setup: Map_AR, GM_SCAR_AR, passthrough config, project defaults."""

import unreal
from pathlib import Path

LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/setup_ar_ios.log")
ENGINE_INI = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Config/DefaultEngine.ini")

GM_AR_TEMPLATE = "/Game/HandheldAR/Blueprints/GameFramework/BP_ARGameMode"
GM_AR = "/Game/SCAR580/Blueprints/GameModes/GM_SCAR_AR"
GM_FP = "/Game/BodycamFPSKIT/Blueprints/GameModes/GM_FP"
BP_FP_CLASS = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter_C"
BP_AR_PC_CLASS = "/Game/HandheldAR/Blueprints/GameFramework/BP_ARPlayerController.BP_ARPlayerController_C"
AR_SESSION = "/Game/HandheldAR/D_ARSessionConfig"
AR_BLANK_MAP = "/Game/HandheldAR/Maps/HandheldARBlankMap"
MAP_AR = "/Game/SCAR580/Maps/Map_AR"
BP_FP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[setup_ar_ios] {msg}")


def ensure_directory(path: str) -> None:
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)
        log(f"Created directory {path}")


def duplicate_asset(source: str, dest: str, label: str) -> unreal.Object | None:
    if unreal.EditorAssetLibrary.does_asset_exist(dest):
        log(f"{label} already exists at {dest}")
        return unreal.load_asset(dest)

    ensure_directory(str(Path(dest).parent).replace("\\", "/"))
    duplicated = unreal.EditorAssetLibrary.duplicate_asset(source, dest)
    if duplicated:
        log(f"Duplicated {label}: {source} -> {dest}")
        return duplicated

    log(f"Failed to duplicate {label} from {source} to {dest}")
    return None


def set_prop(obj, names, value) -> bool:
    for name in names:
        try:
            obj.set_editor_property(name, value)
            log(f"Set {obj.get_name()}.{name} = {value}")
            return True
        except Exception as exc:
            log(f"Skip {name}: {exc}")
    return False


def configure_ar_session_config() -> None:
    config = unreal.load_asset(AR_SESSION)
    if not config:
        raise RuntimeError(f"Missing AR session config at {AR_SESSION}")

    set_prop(config, ("session_type",), unreal.ARSessionType.WORLD)
    set_prop(config, ("bEnableAutomaticCameraOverlay",), True)
    set_prop(config, ("bEnableAutomaticCameraTracking",), False)
    set_prop(config, ("bHorizontalPlaneDetection",), True)
    set_prop(config, ("bVerticalPlaneDetection",), False)
    set_prop(config, ("bEnableAutoFocus",), True)
    set_prop(config, ("bResetCameraTracking",), True)
    set_prop(config, ("bResetTrackedObjects",), True)
    set_prop(config, ("bGenerateMeshDataFromTrackedGeometry",), False)
    unreal.EditorAssetLibrary.save_asset(AR_SESSION, only_if_is_dirty=False)


def configure_game_mode() -> None:
    duplicate_asset(GM_AR_TEMPLATE, GM_AR, "GM_SCAR_AR")
    gm = unreal.load_asset(f"{GM_AR}.GM_SCAR_AR")
    if not gm:
        raise RuntimeError(f"Missing game mode {GM_AR}")

    pawn_class = unreal.load_class(None, BP_FP_CLASS)
    gm_fp = unreal.load_asset(f"{GM_FP}.GM_FP")
    fp_cdo = unreal.get_default_object(gm_fp.generated_class()) if gm_fp else None
    pc_class = fp_cdo.get_editor_property("player_controller_class") if fp_cdo else None
    if not pawn_class or not pc_class:
        raise RuntimeError("Missing BP_FPCharacter or GM_FP player controller")

    cdo = unreal.get_default_object(gm.generated_class())
    set_prop(cdo, ("default_pawn_class", "DefaultPawnClass"), pawn_class)
    set_prop(cdo, ("player_controller_class", "PlayerControllerClass"), pc_class)
    unreal.BlueprintEditorLibrary.compile_blueprint(gm)
    unreal.EditorAssetLibrary.save_asset(GM_AR, only_if_is_dirty=False)
    log("Configured GM_SCAR_AR pawn + player controller")


def configure_fp_character_for_ar() -> None:
    bp = unreal.load_asset(f"{BP_FP}.BP_FPCharacter")
    if not bp:
        raise RuntimeError(f"Missing {BP_FP}")

    cdo = unreal.get_default_object(bp.generated_class())
    set_prop(cdo, ("BODYCAM",), True)

    for comp in cdo.get_components_by_class(unreal.ActorComponent.static_class()):
        class_name = comp.get_class().get_name()
        if "CharacterMovementComponent" in class_name:
            set_prop(comp, ("gravity_scale", "GravityScale"), 0.0)
        if "SpringArmComponent" in class_name:
            set_prop(comp, ("enable_camera_lag", "b_enable_camera_lag"), False)
            set_prop(comp, ("enable_camera_rotation_lag", "b_enable_camera_rotation_lag"), False)
        if any(token in class_name for token in ("PointLightComponent", "SpotLightComponent")):
            set_prop(comp, ("hidden_in_game", "b_hidden_in_game"), False)
            set_prop(comp, ("visible", "b_visible"), True)

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_FP, only_if_is_dirty=False)


def hide_actor(actor) -> None:
    actor.set_actor_hidden_in_game(True)
    actor.set_is_temporarily_hidden_in_editor(True)


def spawn_actor(actor_class, label: str):
    editor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = editor_subsystem.spawn_actor_from_class(
        actor_class,
        unreal.Vector(0.0, 0.0, 0.0),
        unreal.Rotator(0.0, 0.0, 0.0),
    )
    actor.set_actor_label(label)
    log(f"Spawned {label}")
    return actor


def ensure_player_start(world) -> None:
    starts = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PlayerStart.static_class())
    if starts:
        log(f"PlayerStart already present: {starts[0].get_name()}")
        return
    spawn_actor(unreal.PlayerStart, "AR_PlayerStart")


def ensure_ar_origin(world) -> None:
    origin_class = unreal.AROriginActor.static_class()
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, origin_class):
        log(f"AROriginActor already present: {actor.get_name()}")
        return
    spawn_actor(origin_class, "AR_Origin")


def configure_map_ar() -> None:
    duplicate_asset(AR_BLANK_MAP, MAP_AR, "Map_AR")
    unreal.EditorLoadingAndSavingUtils.load_map(MAP_AR)

    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not world:
        raise RuntimeError("Editor world unavailable")

    gm_class = unreal.load_class(None, f"{GM_AR}.GM_SCAR_AR_C")
    if not gm_class:
        raise RuntimeError(f"Missing compiled game mode class for {GM_AR}")

    world.get_world_settings().set_editor_property("default_game_mode", gm_class)
    log("Set Map_AR DefaultGameMode = GM_SCAR_AR")

    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor.static_class()):
        cls = actor.get_class().get_name()
        if cls in {
            "DirectionalLight",
            "SkyLight",
            "ExponentialHeightFog",
            "DocumentationActor",
            "TextRenderActor",
        }:
            hide_actor(actor)
            log(f"Hid {actor.get_name()} ({cls})")

    ensure_player_start(world)
    ensure_ar_origin(world)
    unreal.EditorLoadingAndSavingUtils.save_map(unreal.load_asset(MAP_AR), MAP_AR)


def patch_default_engine_ini() -> None:
    text = ENGINE_INI.read_text()
    replacements = {
        "EditorStartupMap=/Game/BodycamFPSKIT/Maps/Map_Test.Map_Test": "EditorStartupMap=/Game/SCAR580/Maps/Map_AR.Map_AR",
        "GameDefaultMap=/Game/BodycamFPSKIT/Maps/Map_Test.Map_Test": "GameDefaultMap=/Game/SCAR580/Maps/Map_AR.Map_AR",
        "GlobalDefaultGameMode=/Game/BodycamFPSKIT/Blueprints/GameModes/GM_Menu.GM_Menu_C": "GlobalDefaultGameMode=/Game/SCAR580/Blueprints/GameModes/GM_SCAR_AR.GM_SCAR_AR_C",
    }
    for old, new in replacements.items():
        if old in text:
            text = text.replace(old, new)
            log(f"Patched DefaultEngine.ini: {new}")
        elif new.split("=")[0] in text:
            log(f"DefaultEngine.ini already contains {new.split('=')[0]}")
        else:
            log(f"Warning: could not patch {old}")

    ENGINE_INI.write_text(text)


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    ensure_directory("/Game/SCAR580")
    ensure_directory("/Game/SCAR580/Maps")
    ensure_directory("/Game/SCAR580/Blueprints/GameModes")

    required = [AR_SESSION, AR_BLANK_MAP, GM_AR_TEMPLATE, BP_FP, "/Game/HandheldAR/Blueprints/GameFramework/BP_ARPlayerController"]
    missing = [path for path in required if not unreal.EditorAssetLibrary.does_asset_exist(path)]
    if missing:
        raise RuntimeError(f"Missing required assets: {missing}")

    configure_ar_session_config()
    configure_game_mode()
    configure_fp_character_for_ar()
    patch_default_engine_ini()
    log("SCAR-580 AR core setup complete (run finish_ar_map.py for Map_AR if needed)")


main()
