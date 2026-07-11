"""Inspect ToggleLaser/ToggleFlashlight function graphs on item base."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_toggle_laser.log")
lines = []

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for fname in ("ToggleLaser", "ToggleFlashlight"):
    graph = None
    for g in unreal.BlueprintEditorLibrary.list_graphs(item):
        if g.get_name() == fname:
            graph = g
            break
    lines.append(f"\n=== {fname} graph={graph} ===")
    if not graph:
        continue
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    for node in ed.list_all_nodes()[:35]:
        lines.append(f"  {node.get_name()} | {node.get_node_title()}")

OUT.write_text("\n".join(lines))
