"""Dump ABP_Mirror anim graph nodes and find manny-skeleton weapon anims."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_mirror_graph.log")
lines = []


def log(msg):
    lines.append(str(msg))


# 1. ABP_Mirror graph nodes
abp = unreal.load_asset("/Game/BodycamFPSKIT/Demo/Character/Mannequins/Animations/ABP_Mirror.ABP_Mirror")
log(f"ABP_Mirror loaded: {bool(abp)}")
if abp:
    try:
        graphs = unreal.BlueprintEditorLibrary.list_graphs(abp)
        for g in graphs:
            log(f"=== graph {g.get_name()} ===")
            try:
                ged = unreal.BlueprintGraphEditor.get_graph_editor(g)
                for node in ged.list_all_nodes():
                    title = str(node.get_node_title()).replace("\n", " | ")
                    log(f"  {node.get_name()} | {title}")
            except Exception as exc:
                log(f"  graph editor err: {exc}")
    except Exception as exc:
        log(f"list_graphs err: {exc}")

# 2. Manny skeleton weapon-related animations anywhere in the project
manny_mesh = unreal.load_asset("/Game/BodycamFPSKIT/Demo/Character/Mannequins/Meshes/SKM_Manny.SKM_Manny")
manny_skel = manny_mesh.get_editor_property("skeleton") if manny_mesh else None
log(f"=== manny skeleton: {manny_skel.get_path_name() if manny_skel else None} ===")

registry = unreal.AssetRegistryHelpers.get_asset_registry()
filt = unreal.ARFilter(class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "AnimSequence")], recursive_paths=True, package_paths=["/Game"])
assets = registry.get_assets(filt)
log(f"total anim sequences: {len(assets)}")
count = 0
for ad in assets:
    name = str(ad.asset_name)
    if not any(k in name.lower() for k in ("pistol", "rifle", "gun", "weapon", "aim", "fire", "shoot")):
        continue
    seq = ad.get_asset()
    skel = seq.get_editor_property("skeleton") if seq else None
    skel_name = skel.get_name() if skel else "?"
    log(f"  {name} skel={skel_name} path={ad.package_name}")
    count += 1
    if count > 120:
        log("  ... truncated")
        break

OUT.write_text("\n".join(lines))
print("probe complete")
