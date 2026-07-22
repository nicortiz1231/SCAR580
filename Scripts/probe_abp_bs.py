"""Probe AnimGraph node access and rename_referencing_soft_object_paths signature."""

from __future__ import annotations

import inspect
from pathlib import Path

import unreal

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_abp_bs.log")
OUT_ABP = "/Game/SCAR580/Zombies/ABP_Enemy_Pack"
OUT_BS = "/Game/SCAR580/Zombies/BS_Walk_Speed_Pack"
KIT_BS = "/Game/FirstPersonHorrorKit/Characters/Enemy/BS_Walk_Speed"


def log(msg: str) -> None:
    prev = LOG.read_text(encoding="utf-8") if LOG.exists() else ""
    LOG.write_text(prev + msg + "\n", encoding="utf-8")
    print(msg)
    try:
        unreal.log(str(msg))
    except Exception:
        pass


def main():
    if LOG.exists():
        LOG.unlink()
    log("=== probe ===")

    at = unreal.AssetToolsHelpers.get_asset_tools()
    fn = at.rename_referencing_soft_object_paths
    log(f"rename_referencing_soft_object_paths={fn}")
    try:
        log(f"doc={fn.__doc__}")
    except Exception as exc:
        log(f"doc err {exc}")
    try:
        log(f"sig={inspect.signature(fn)}")
    except Exception as exc:
        log(f"sig err {exc}")

    abp = unreal.EditorAssetLibrary.load_asset(OUT_ABP)
    pack_bs = unreal.EditorAssetLibrary.load_asset(OUT_BS)
    log(f"abp={abp} pack_bs={pack_bs}")

    graph = unreal.BlueprintEditorLibrary.find_graph(abp, "AnimGraph")
    log(f"graph={graph} type={type(graph)}")

    # Try BlueprintGraphEditor
    try:
        editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        log(f"editor={editor}")
        nodes = list(editor.list_all_nodes())
        log(f"list_all_nodes count={len(nodes)}")
        for n in nodes:
            cls = n.get_class().get_name()
            log(f"  {n.get_name()} {cls}")
            if "Blend" in cls:
                log(f"  *** BLEND ***")
                # Inspect UObject properties via get_editor_property
                for prop in (
                    "node", "Node", "blend_space", "BlendSpace",
                    "blend_space_asset", "BlendSpaceAsset",
                ):
                    try:
                        v = n.get_editor_property(prop)
                        log(f"    {prop}={v}")
                    except Exception as exc:
                        log(f"    {prop} ERR {exc}")
                # Try nested
                try:
                    node_struct = n.get_editor_property("node")
                    log(f"    node_struct type={type(node_struct)}")
                    # For FAnimNode_BlendSpacePlayer, BlendSpace is TObjectPtr<UBlendSpace>
                    for bp in ("blend_space", "BlendSpace"):
                        try:
                            old = node_struct.get_editor_property(bp)
                            log(f"    nested {bp}={old}")
                            node_struct.set_editor_property(bp, pack_bs)
                            n.set_editor_property("node", node_struct)
                            log(f"    SET nested {bp}")
                        except Exception as exc:
                            log(f"    nested {bp} ERR {exc}")
                except Exception as exc:
                    log(f"    node nested ERR {exc}")
    except Exception as exc:
        log(f"BlueprintGraphEditor path ERR: {exc}")

    # Try graph.nodes with try
    try:
        nodes2 = graph.get_editor_property("nodes")
        log(f"graph.nodes prop count={len(list(nodes2))}")
    except Exception as exc:
        log(f"graph.nodes prop ERR: {exc}")

    try:
        nodes3 = list(graph.nodes)
        log(f"graph.nodes attr count={len(nodes3)}")
    except Exception as exc:
        log(f"graph.nodes attr ERR: {exc}")

    # Try rename with correct arity
    try:
        # Maybe: rename_referencing_soft_object_paths(Array of SoftObjectPath renames)
        # Or single dict
        old = unreal.SoftObjectPath(f"{KIT_BS}.{KIT_BS.split('/')[-1]}")
        new = unreal.SoftObjectPath(f"{OUT_BS}.{OUT_BS.split('/')[-1]}")
        log(f"trying SoftObjectPath pair {old} -> {new}")
        # Attempt 1-arg
        try:
            r = fn([(old, new)])
            log(f"1-arg list of tuples: {r}")
        except Exception as exc:
            log(f"1-arg tuples: {exc}")
        try:
            r = fn([old], [new])
            log(f"2-arg lists: {r}")
        except Exception as exc:
            log(f"2-arg lists: {exc}")
        try:
            # AssetRenameData?
            if hasattr(unreal, "AssetRenameData"):
                log("AssetRenameData exists")
            if hasattr(unreal, "SoftObjectPathRenamePair"):
                log("SoftObjectPathRenamePair exists")
            for name in dir(unreal):
                if "Rename" in name and "Soft" in name:
                    log(f"  unreal.{name}")
                if name == "AssetRenameData":
                    log(f"  AssetRenameData docs")
        except Exception as exc:
            log(f"type hunt: {exc}")
    except Exception as exc:
        log(f"rename attempts: {exc}")

    # Compile/save if we swapped
    try:
        unreal.BlueprintEditorLibrary.compile_blueprint(abp)
        unreal.EditorAssetLibrary.save_asset(OUT_ABP, only_if_is_dirty=False)
    except Exception as exc:
        log(f"compile/save: {exc}")

    refs_kit = unreal.EditorAssetLibrary.find_package_referencers_for_asset(KIT_BS, False)
    refs_pack = unreal.EditorAssetLibrary.find_package_referencers_for_asset(OUT_BS, False)
    log(f"kit refs={list(refs_kit) if refs_kit else None}")
    log(f"pack refs={list(refs_pack) if refs_pack else None}")
    log("=== done ===")


main()
