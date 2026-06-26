"""Dump pickup overlap + item AimDownSight + all item graphs for sight logic."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_pickup_aimdown.log")
lines = []

pickup = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Pickup_Sniper.BP_Weapon_Pickup_Sniper")
for g in unreal.BlueprintEditorLibrary.list_graphs(pickup):
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append(f"=== pickup graph {g.get_name()} ({len(ed.list_all_nodes())} nodes) ===")
    for node in ed.list_all_nodes():
        t = str(node.get_node_title()).replace("\n", " | ")
        if any(k in t for k in ("Overlap", "Pickup", "ItemData", "Equip", "Add", "Spawn", "Weapon", "Sight", "Attach")):
            lines.append(f"  {node.get_name()} | {t}")

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    hits = []
    for node in ed.list_all_nodes():
        t = str(node.get_node_title()).replace("\n", " | ")
        if any(k in t for k in ("ScopeSight", "OpticSight", "SetStaticMesh", "ENUM_Sights", "Sight", "SpawnAttachment")):
            hits.append(f"  {node.get_name()} | {t}")
    if hits:
        lines.append(f"=== item {g.get_name()} ===")
        lines.extend(hits)

OUT.write_text("\n".join(lines))
