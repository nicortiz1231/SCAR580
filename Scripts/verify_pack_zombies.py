"""Verify pack zombie assets and try a short PIE spawn check on Map_AR."""

from __future__ import annotations

import time
from pathlib import Path

import unreal

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/verify_pack_zombies.log")

ASSETS = [
    "/Game/SCAR580/Zombies/BS_Walk_Speed_Pack",
    "/Game/SCAR580/Zombies/ABP_Enemy_Pack",
    "/Game/SCAR580/Zombies/anim_Attack_A_Montage_Pack",
    "/Game/SCAR580/Zombies/BP_Enemy_ZombiePack",
    "/Game/ZombieAnimationPack/Animations/Mannequin_UE5/anim_Idle_A",
    "/Game/ZombieAnimationPack/Animations/Mannequin_UE5/anim_Run_A",
    "/Game/ZombieAnimationPack/Animations/Mannequin_UE5/anim_Attack_A",
]


def log(msg: str) -> None:
    prev = LOG.read_text(encoding="utf-8") if LOG.exists() else ""
    LOG.write_text(prev + msg + "\n", encoding="utf-8")
    print(msg)
    unreal.log(f"[verify_pack] {msg}")


def main():
    if LOG.exists():
        LOG.unlink()
    log("=== verify pack zombies ===")

    for path in ASSETS:
        ok = unreal.EditorAssetLibrary.does_asset_exist(path)
        log(f"asset {path} exists={ok}")

    # Blend space samples
    bs = unreal.EditorAssetLibrary.load_asset("/Game/SCAR580/Zombies/BS_Walk_Speed_Pack")
    for i, sample in enumerate(list(bs.get_editor_property("sample_data"))):
        anim = sample.get_editor_property("animation")
        log(f"BS[{i}]={anim.get_path_name() if anim else None}")

    # ABP blend space
    abp = unreal.EditorAssetLibrary.load_asset("/Game/SCAR580/Zombies/ABP_Enemy_Pack")
    graph = unreal.BlueprintEditorLibrary.find_graph(abp, "AnimGraph")
    editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    for n in list(editor.list_all_nodes()):
        if n.get_class().get_name() == "AnimGraphNode_BlendSpacePlayer":
            bso = n.get_editor_property("node").get_editor_property("blend_space")
            log(f"ABP BlendSpace={bso.get_path_name() if bso else None}")

    # Montage
    mont = unreal.EditorAssetLibrary.load_asset("/Game/SCAR580/Zombies/anim_Attack_A_Montage_Pack")
    track = list(mont.get_editor_property("slot_anim_tracks"))[0]
    seg = list(track.get_editor_property("anim_track").get_editor_property("anim_segments"))[0]
    anim = seg.get_editor_property("anim_reference")
    log(f"Montage anim={anim.get_path_name() if anim else None}")

    # BP class load
    bp = unreal.EditorAssetLibrary.load_asset("/Game/SCAR580/Zombies/BP_Enemy_ZombiePack")
    cls = bp.generated_class()
    log(f"BP class={cls}")
    cdo = unreal.get_default_object(cls)
    mesh = cdo.get_editor_property("mesh")
    log(f"BP mesh.anim_class={mesh.get_editor_property('anim_class') if mesh else None}")

    # Open Map_AR and PIE briefly
    map_path = "/Game/SCAR580/Maps/Map_AR"
    if not unreal.EditorAssetLibrary.does_asset_exist(map_path):
        # try alternate
        for alt in ("/Game/Maps/Map_AR", "/Game/FirstPersonHorrorKit/Maps/Map_AR"):
            if unreal.EditorAssetLibrary.does_asset_exist(alt):
                map_path = alt
                break
    log(f"map={map_path} exists={unreal.EditorAssetLibrary.does_asset_exist(map_path)}")

    try:
        unreal.EditorLoadingAndSavingUtils.load_map(map_path)
        log("map loaded")
    except Exception as exc:
        log(f"load_map: {exc}")
        try:
            unreal.EditorLevelLibrary.load_level(map_path)
            log("load_level ok")
        except Exception as exc2:
            log(f"load_level: {exc2}")

    # Start PIE
    try:
        pie = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        pie.editor_request_begin_play()
        log("PIE begin requested")
    except Exception as exc:
        log(f"PIE begin: {exc}")
        try:
            unreal.EditorLevelLibrary.editor_play_simulate()
            log("editor_play_simulate")
        except Exception as exc2:
            log(f"simulate: {exc2}")

    # Poll for director spawn log by checking world actors
    found_kit = 0
    found_pack = 0
    for attempt in range(40):
        time.sleep(0.5)
        try:
            world = unreal.EditorLevelLibrary.get_editor_world()
            # During PIE, need PIE world
            try:
                pie_worlds = unreal.EditorLevelLibrary.get_pie_worlds(False)
                if pie_worlds:
                    world = list(pie_worlds)[0]
            except Exception:
                pass
            actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Character)
            found_kit = 0
            found_pack = 0
            names = []
            for a in list(actors or []):
                name = a.get_name()
                cname = a.get_class().get_name()
                names.append(f"{name}|{cname}")
                if "ZombiePack" in cname or "ZombiePack" in name:
                    found_pack += 1
                elif cname.startswith("BP_Enemy_C") or cname == "BP_Enemy_C":
                    found_kit += 1
            if found_kit or found_pack:
                log(f"attempt {attempt}: kit={found_kit} pack={found_pack}")
                if found_kit >= 5 and found_pack >= 5:
                    break
            if attempt in (0, 5, 10, 20, 39):
                log(f"attempt {attempt}: chars={len(names)} sample={names[:12]}")
        except Exception as exc:
            log(f"poll {attempt}: {exc}")

    log(f"FINAL kit={found_kit} pack={found_pack}")

    # End PIE
    try:
        pie = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        pie.editor_request_end_play()
        log("PIE end requested")
    except Exception as exc:
        log(f"PIE end: {exc}")

    log("=== done ===")


main()
