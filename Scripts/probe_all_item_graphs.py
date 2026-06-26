"""List all item/sniper graphs and find attachment mesh selection."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_all_item_graphs.log")
lines = []

for path in (
    "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper",
):
    bp = unreal.load_asset(path)
    lines.append(f"=== {path.split('/')[-1]} ===")
    for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
        editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
        mesh_nodes = 0
        for node in editor.list_all_nodes():
            title = str(node.get_node_title())
            if "SetStaticMesh" in title or "ENUM_Sights" in title or "ScopeSight" in title:
                mesh_nodes += 1
        lines.append(f"  {g.get_name()} ({len(editor.list_all_nodes())} nodes, {mesh_nodes} sight/mesh)")

# full AkimboSelector if exists
item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    if "Selector" not in g.get_name() and "Attach" not in g.get_name():
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append(f"=== DETAIL {g.get_name()} ===")
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        lines.append(f"  {node.get_name()} | {title}")

OUT.write_text("\n".join(lines))
