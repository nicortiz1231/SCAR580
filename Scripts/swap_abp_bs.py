"""Persist ABP_Enemy_Pack BlendSpacePlayer -> BS_Walk_Speed_Pack."""

from __future__ import annotations

from pathlib import Path

import unreal

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/swap_abp_bs.log")
OUT_ABP = "/Game/SCAR580/Zombies/ABP_Enemy_Pack"
OUT_BS = "/Game/SCAR580/Zombies/BS_Walk_Speed_Pack"
KIT_BS = "/Game/FirstPersonHorrorKit/Characters/Enemy/BS_Walk_Speed"


def log(msg: str) -> None:
    prev = LOG.read_text(encoding="utf-8") if LOG.exists() else ""
    LOG.write_text(prev + msg + "\n", encoding="utf-8")
    print(msg)
    unreal.log(f"[swap_abp_bs] {msg}")


def read_bs(abp_path: str):
    abp = unreal.EditorAssetLibrary.load_asset(abp_path)
    graph = unreal.BlueprintEditorLibrary.find_graph(abp, "AnimGraph")
    editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    for n in list(editor.list_all_nodes()):
        if n.get_class().get_name() != "AnimGraphNode_BlendSpacePlayer":
            continue
        node_struct = n.get_editor_property("node")
        bs = node_struct.get_editor_property("blend_space")
        return bs.get_path_name() if bs else None
    return None


def main():
    if LOG.exists():
        LOG.unlink()
    log("=== start ===")
    log(f"BEFORE {read_bs(OUT_ABP)}")

    abp = unreal.EditorAssetLibrary.load_asset(OUT_ABP)
    pack_bs = unreal.EditorAssetLibrary.load_asset(OUT_BS)

    with unreal.ScopedEditorTransaction("SCAR Swap Pack BlendSpace"):
        graph = unreal.BlueprintEditorLibrary.find_graph(abp, "AnimGraph")
        editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        for n in list(editor.list_all_nodes()):
            if n.get_class().get_name() != "AnimGraphNode_BlendSpacePlayer":
                continue
            node_struct = n.get_editor_property("node")
            old = node_struct.get_editor_property("blend_space")
            log(f"old={old.get_path_name() if old else None}")
            node_struct.set_editor_property("blend_space", pack_bs)
            n.set_editor_property("node", node_struct)
            # Also try Node (capital)
            try:
                n.set_editor_property("Node", node_struct)
            except Exception as exc:
                log(f"Node capital: {exc}")
            # Force notify
            try:
                n.post_edit_change()
            except Exception as exc:
                log(f"post_edit_change: {exc}")
            mid = n.get_editor_property("node").get_editor_property("blend_space")
            log(f"mid-read={mid.get_path_name() if mid else None}")

        try:
            abp.modify()
        except Exception as exc:
            log(f"modify: {exc}")

    # Save BEFORE compile
    unreal.EditorAssetLibrary.save_loaded_asset(abp)
    unreal.EditorAssetLibrary.save_asset(OUT_ABP, only_if_is_dirty=False)
    log(f"AFTER SAVE (no compile) {read_bs(OUT_ABP)}")

    # Reload from disk
    unreal.EditorAssetLibrary.load_asset(OUT_ABP)
    log(f"AFTER RELOAD {read_bs(OUT_ABP)}")

    abp = unreal.EditorAssetLibrary.load_asset(OUT_ABP)
    unreal.BlueprintEditorLibrary.compile_blueprint(abp)
    unreal.EditorAssetLibrary.save_asset(OUT_ABP, only_if_is_dirty=False)
    log(f"AFTER COMPILE {read_bs(OUT_ABP)}")

    # Asset registry referencers
    unreal.AssetRegistryHelpers.get_asset_registry().scan_paths_synchronous([OUT_ABP.rsplit('/', 1)[0]], True)
    refs_kit = unreal.EditorAssetLibrary.find_package_referencers_for_asset(KIT_BS, False)
    refs_pack = unreal.EditorAssetLibrary.find_package_referencers_for_asset(OUT_BS, False)
    log(f"kit refs={list(refs_kit) if refs_kit else None}")
    log(f"pack refs={list(refs_pack) if refs_pack else None}")

    # Soft path rename as extra (won't fix hard refs but harmless)
    try:
        at = unreal.AssetToolsHelpers.get_asset_tools()
        pkg = unreal.load_package(OUT_ABP)
        packages = unreal.Array(unreal.Package)
        packages.append(pkg)
        old = unreal.SoftObjectPath(f"{KIT_BS}.{KIT_BS.split('/')[-1]}")
        new = unreal.SoftObjectPath(f"{OUT_BS}.{OUT_BS.split('/')[-1]}")
        redirect = unreal.Map(unreal.SoftObjectPath, unreal.SoftObjectPath)
        redirect[old] = new
        log(f"soft old empty? {old}")
        at.rename_referencing_soft_object_paths(packages, redirect)
        log("soft rename done")
    except Exception as exc:
        log(f"soft rename: {exc}")

    log("=== done ===")


main()
