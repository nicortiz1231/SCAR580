import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_item_graphs.log")
lines = []

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    lines.append(g.get_name())
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if any(k in title for k in ("SpawnAttachment", "OpticSight", "ScopeSight", "Sight", "Switch")):
            lines.append(f"  {node.get_name()} | {title}")

sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
lines.append("=== Sniper graphs ===")
for g in unreal.BlueprintEditorLibrary.list_graphs(sniper):
    lines.append(g.get_name())
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if any(k in title for k in ("SpawnAttachment", "OpticSight", "ScopeSight", "Sight", "Aim", "ItemData")):
            lines.append(f"  {node.get_name()} | {title}")

OUT.write_text("\n".join(lines))
