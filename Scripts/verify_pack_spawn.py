"""PIE Map_AR, PlaceAt AR ground, confirm kit+pack zombie spawn counts."""

from __future__ import annotations

import time
from pathlib import Path

import unreal

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/verify_pack_spawn.log")
MAP = "/Game/SCAR580/Maps/Map_AR"


def log(msg: str) -> None:
    prev = LOG.read_text(encoding="utf-8") if LOG.exists() else ""
    LOG.write_text(prev + msg + "\n", encoding="utf-8")
    print(msg)
    unreal.log(f"[verify_pack_spawn] {msg}")


def get_pie_world():
    try:
        worlds = unreal.EditorLevelLibrary.get_pie_world_context()
    except Exception:
        worlds = None
    try:
        pie = list(unreal.EditorLevelLibrary.get_pie_worlds(False) or [])
        if pie:
            return pie[0]
    except Exception as exc:
        log(f"get_pie_worlds: {exc}")
    # Fallback
    try:
        return unreal.UnrealEditorSubsystem().get_game_world()
    except Exception:
        pass
    try:
        return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    except Exception as exc:
        log(f"get_game_world: {exc}")
    return None


def count_enemies(world):
    kit = pack = 0
    names = []
    if not world:
        return 0, 0, names
    actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Character) or []
    for a in list(actors):
        cname = a.get_class().get_name()
        names.append(cname)
        if "ZombiePack" in cname:
            pack += 1
        elif cname == "BP_Enemy_C":
            kit += 1
    return kit, pack, names


def main():
    if LOG.exists():
        LOG.unlink()
    log("=== verify pack spawn ===")

    # End any existing PIE
    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
        time.sleep(1.0)
    except Exception:
        pass

    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    log("map loaded")

    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play()
    log("PIE started")

    world = None
    for i in range(30):
        time.sleep(0.4)
        world = get_pie_world()
        if world:
            log(f"PIE world at {i}: {world}")
            break
    if not world:
        log("NO PIE WORLD")
        log("=== done ===")
        return

    # Find or spawn AR ground and PlaceAt
    ground_cls = unreal.load_class(None, "/Script/SCAR.SCARSharedARGround")
    log(f"ground_cls={ground_cls}")
    grounds = list(unreal.GameplayStatics.get_all_actors_of_class(world, ground_cls) or [])
    log(f"existing grounds={len(grounds)}")
    if grounds:
        ground = grounds[0]
    else:
        ground = world.spawn_actor(ground_cls, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
        log(f"spawned ground={ground}")

    # PlaceAt(OriginXY, SurfaceWorldZ)
    try:
        ground.place_at(unreal.Vector(0, 0, 0), 0.0)
        log("place_at called")
    except Exception as exc:
        log(f"place_at: {exc}")
        # try PlaceAt Pascal
        try:
            ground.call_method("PlaceAt", (unreal.Vector(0, 0, 0), 0.0))
            log("PlaceAt call_method ok")
        except Exception as exc2:
            log(f"PlaceAt call_method: {exc2}")

    kit = pack = 0
    for i in range(40):
        time.sleep(0.35)
        kit, pack, names = count_enemies(world)
        if i % 5 == 0 or (kit + pack) > 0:
            log(f"t={i} kit={kit} pack={pack} sample={names[:15]}")
        if kit >= 5 and pack >= 5:
            break

    # Also look for director
    dir_cls = unreal.load_class(None, "/Script/SCAR.SCARHorrorKitZombieDirector")
    directors = list(unreal.GameplayStatics.get_all_actors_of_class(world, dir_cls) or [])
    log(f"directors={len(directors)} kit={kit} pack={pack}")

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
    except Exception:
        pass
    log("=== done ===")


main()
