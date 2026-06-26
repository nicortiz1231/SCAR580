"""Find ENUM_Sights switch and SetStaticMesh in entire item BP."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_item_sight_switch.log")
lines = []

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    hits = []
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if "ENUM_Sights" in title or ("SetStaticMesh" in title and "SpareMag" not in title):
            hits.append(f"  {node.get_name()} | {title}")
    if hits:
        lines.append(f"=== {g.get_name()} ===")
        lines.extend(hits)

# Also check sniper for any hidden graphs via parent
sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
parent = sniper.get_editor_property("parent_class")
lines.append(f"sniper parent={parent}")

OUT.write_text("\n".join(lines))
