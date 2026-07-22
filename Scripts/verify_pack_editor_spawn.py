"""Editor-world spawn test: PlaceAt AR ground and count kit+pack zombies."""

from __future__ import annotations

import time
from pathlib import Path

import unreal

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/verify_pack_editor_spawn.log")


def log(msg: str) -> None:
    prev = LOG.read_text(encoding="utf-8") if LOG.exists() else ""
    LOG.write_text(prev + msg + "\n", encoding="utf-8")
    print(msg)
    unreal.log(f"[verify_pack_editor] {msg}")


def main():
    if LOG.exists():
        LOG.unlink()
    log("=== editor spawn verify ===")

    # Stop PIE if any
    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
        time.sleep(0.5)
    except Exception:
        pass

    unreal.EditorLoadingAndSavingUtils.load_map("/Game/SCAR580/Maps/Map_AR")
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    log(f"world={world}")

    ground_cls = unreal.load_class(None, "/Script/SCAR.SCARSharedARGround")
    dir_cls = unreal.load_class(None, "/Script/SCAR.SCARHorrorKitZombieDirector")
    kit_cls = unreal.load_class(None, "/Game/FirstPersonHorrorKit/Blueprints/Enemy/BP_Enemy.BP_Enemy_C")
    pack_cls = unreal.load_class(None, "/Game/SCAR580/Zombies/BP_Enemy_ZombiePack.BP_Enemy_ZombiePack_C")
    log(f"ground_cls={ground_cls}")
    log(f"dir_cls={dir_cls}")
    log(f"kit_cls={kit_cls}")
    log(f"pack_cls={pack_cls}")

    if not pack_cls:
        log("FAIL: pack class failed to load")
        log("=== done ===")
        return

    # Clean prior test actors
    for cls in (dir_cls, ground_cls, kit_cls, pack_cls):
        if not cls:
            continue
        for a in list(unreal.GameplayStatics.get_all_actors_of_class(world, cls) or []):
            try:
                a.destroy_actor()
            except Exception:
                pass

    ground = unreal.EditorLevelLibrary.spawn_actor_from_class(
        ground_cls, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)
    )
    log(f"ground={ground}")

    # PlaceAt should EnsureInWorld director + SyncToGround -> spawn
    try:
        ground.place_at(unreal.Vector(0.0, 0.0, 0.0), 0.0)
        log("place_at ok")
    except Exception as exc:
        log(f"place_at failed: {exc}")
        # Manual ensure + sync
        director = unreal.EditorLevelLibrary.spawn_actor_from_class(
            dir_cls, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)
        )
        log(f"manual director={director}")
        try:
            director.sync_to_ground(ground)
            log("sync_to_ground ok")
        except Exception as exc2:
            log(f"sync_to_ground: {exc2}")

    time.sleep(0.5)

    kit = list(unreal.GameplayStatics.get_all_actors_of_class(world, kit_cls) or [])
    pack = list(unreal.GameplayStatics.get_all_actors_of_class(world, pack_cls) or [])
    dirs = list(unreal.GameplayStatics.get_all_actors_of_class(world, dir_cls) or [])
    log(f"kit_count={len(kit)} pack_count={len(pack)} directors={len(dirs)}")
    for a in kit[:3]:
        log(f"  kit {a.get_name()} loc={a.get_actor_location()}")
    for a in pack[:3]:
        mesh = a.get_editor_property("mesh") if hasattr(a, "get_editor_property") else None
        try:
            mesh = a.get_component_by_class(unreal.SkeletalMeshComponent)
        except Exception:
            mesh = a.mesh if hasattr(a, "mesh") else None
        anim = None
        try:
            anim = mesh.get_anim_class() if mesh else None
        except Exception:
            try:
                anim = mesh.get_editor_property("anim_class")
            except Exception:
                pass
        log(f"  pack {a.get_name()} loc={a.get_actor_location()} anim={anim}")

    ok = len(kit) >= 5 and len(pack) >= 5
    log(f"PASS={ok}")

    # Cleanup so map isn't dirty with 10 zombies
    for a in kit + pack + dirs + [ground]:
        try:
            if a:
                a.destroy_actor()
        except Exception:
            pass
    log("cleaned up")
    log("=== done ===")


main()
