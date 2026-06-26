import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sniper_all_graphs.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
lines.append("=== graphs ===")
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    nodes = editor.list_all_nodes()
    lines.append(f"  {g.get_name()} ({len(nodes)} nodes)")
    for node in nodes:
        title = str(node.get_node_title()).replace("\n", " | ")
        lines.append(f"    {node.get_name()} | {title}")

OUT.write_text("\n".join(lines))
