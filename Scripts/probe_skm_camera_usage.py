"""Find every asset that references SKM_Camera / ABP_FP_ArmsProcedural, and
check whether BP_FPCharacter's construction script or BeginSetup macro
dynamically spawns any extra skeletal mesh component at runtime (which
wouldn't show up in a static SCS component probe)."""
import unreal
from pathlib import Path

LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_skm_camera_usage.log")
TARGETS = (
    "/Game/BodycamFPSKIT/Blueprints/Camera/SKM_Camera",
    "/Game/BodycamFPSKIT/Character/ABP_FP_ArmsProcedural",
)
BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"


def log(msg: str) -> None:
    with LOG_PATH.open("a") as f:
        f.write(str(msg) + "\n")
    unreal.log(f"[probe_skm_camera_usage] {msg}")


if LOG_PATH.exists():
    LOG_PATH.unlink()

registry = unreal.AssetRegistryHelpers.get_asset_registry()

for target in TARGETS:
    log(f"\n=== Referencers of {target} ===")
    exists = unreal.EditorAssetLibrary.does_asset_exist(target)
    log(f"exists={exists}")
    if not exists:
        continue
    refs = registry.get_referencers(target, unreal.AssetRegistryDependencyOptions())
    for r in refs:
        log(f"  {r}")

log("\n=== Checking BP_FPCharacter graphs for dynamic skeletal mesh creation ===")
bp = unreal.load_asset(BP_ASSET)
if bp:
    for graph in unreal.BlueprintEditorLibrary.list_graphs(bp):
        gname = graph.get_name()
        editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        for node in editor.list_all_nodes():
            cls = node.get_class().get_name()
            if cls in ("K2Node_AddComponentByClass", "K2Node_AddComponent", "K2Node_ConstructObjectFromClass"):
                log(f"  Graph={gname} Node={node.get_name()} Class={cls}")

log("\nDONE")
