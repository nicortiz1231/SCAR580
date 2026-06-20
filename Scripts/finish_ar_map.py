"""Finish Map_AR setup only."""

import unreal
from pathlib import Path

LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/finish_ar_map.log")
ENGINE_INI = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Config/DefaultEngine.ini")

GM_AR = "/Game/SCAR580/Blueprints/GameModes/GM_SCAR_AR"
AR_BLANK_MAP = "/Game/HandheldAR/Maps/HandheldARBlankMap"
MAP_AR = "/Game/SCAR580/Maps/Map_AR"


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[finish_ar_map] {msg}")


def hide_actor(actor) -> None:
    actor.set_actor_hidden_in_game(True)
    actor.set_is_temporarily_hidden_in_editor(True)


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    if not unreal.EditorAssetLibrary.does_directory_exist("/Game/SCAR580/Maps"):
        unreal.EditorAssetLibrary.make_directory("/Game/SCAR580/Maps")

    if not unreal.EditorAssetLibrary.does_asset_exist(MAP_AR):
        duplicated = unreal.EditorAssetLibrary.duplicate_asset(AR_BLANK_MAP, MAP_AR)
        if not duplicated:
            raise RuntimeError(f"Failed to duplicate map to {MAP_AR}")
        log(f"Duplicated map to {MAP_AR}")
    else:
        log(f"Map already exists at {MAP_AR}")

    unreal.EditorLoadingAndSavingUtils.load_map(MAP_AR)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not world:
        raise RuntimeError("No editor world")

    gm_class = unreal.load_class(None, f"{GM_AR}.GM_SCAR_AR_C")
    world.get_world_settings().set_editor_property("default_game_mode", gm_class)
    log("Applied GM_SCAR_AR to world settings")

    editor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor.static_class()):
        cls = actor.get_class().get_name()
        # Keep DirectionalLight/SkyLight visible for Mac PIE preview; hide template clutter only.
        if cls in {"ExponentialHeightFog", "DocumentationActor", "TextRenderActor"}:
            hide_actor(actor)
            log(f"Hid {actor.get_name()}")

    if not unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PlayerStart.static_class()):
        ps = editor_subsystem.spawn_actor_from_class(
            unreal.PlayerStart, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)
        )
        ps.set_actor_label("AR_PlayerStart")
        log("Spawned PlayerStart")

    if not unreal.GameplayStatics.get_all_actors_of_class(world, unreal.AROriginActor.static_class()):
        origin = editor_subsystem.spawn_actor_from_class(
            unreal.AROriginActor.static_class(), unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)
        )
        origin.set_actor_label("AR_Origin")
        log("Spawned AROriginActor")

    pistol_class = unreal.load_class(
        None,
        "/Game/BodycamFPSKIT/Blueprints/Interactables/Pistol/BP_Weapon_Pickup_Pistol.BP_Weapon_Pickup_Pistol_C",
    )
    rifle_class = unreal.load_class(
        None,
        "/Game/BodycamFPSKIT/Blueprints/Interactables/AmericanRifle/BP_Weapon_Pickup_AmericanRifle.BP_Weapon_Pickup_AmericanRifle_C",
    )
    actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor.static_class())
    has_pistol = any("BP_Weapon_Pickup_Pistol" in a.get_class().get_name() for a in actors)
    has_rifle = any("BP_Weapon_Pickup_AmericanRifle" in a.get_class().get_name() for a in actors)
    ps = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PlayerStart.static_class())
    loc = ps[0].get_actor_location() if ps else unreal.Vector(0, 0, 0)
    rot = ps[0].get_actor_rotation() if ps else unreal.Rotator(0, 0, 0)
    if pistol_class and not has_pistol:
        pickup = editor_subsystem.spawn_actor_from_class(pistol_class, loc, rot)
        pickup.set_actor_label("AR_StartingPistol")
        log("Spawned AR_StartingPistol for default loadout")
    if rifle_class and not has_rifle:
        pickup = editor_subsystem.spawn_actor_from_class(rifle_class, loc, rot)
        pickup.set_actor_label("AR_StartingRifle")
        log("Spawned AR_StartingRifle for secondary weapon")

    unreal.EditorLoadingAndSavingUtils.save_current_level()
    log("Saved Map_AR")

    text = ENGINE_INI.read_text()
    text = text.replace(
        "EditorStartupMap=/Game/BodycamFPSKIT/Maps/Map_Test.Map_Test",
        "EditorStartupMap=/Game/SCAR580/Maps/Map_AR.Map_AR",
    )
    text = text.replace(
        "GameDefaultMap=/Game/BodycamFPSKIT/Maps/Map_Test.Map_Test",
        "GameDefaultMap=/Game/SCAR580/Maps/Map_AR.Map_AR",
    )
    text = text.replace(
        "GlobalDefaultGameMode=/Game/BodycamFPSKIT/Blueprints/GameModes/GM_Menu.GM_Menu_C",
        "GlobalDefaultGameMode=/Game/SCAR580/Blueprints/GameModes/GM_SCAR_AR.GM_SCAR_AR_C",
    )
    ENGINE_INI.write_text(text)
    log("Patched DefaultEngine.ini")
    log("Done")


main()
