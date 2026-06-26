"""Trace pickup PrimaryEquip -> weapon spawn -> scope in original Bodycam."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_orig_pickup_equip.log")
lines = []

pickup = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Pickup.BP_Item_Pickup")
ped = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(pickup))

def walk_from(node, depth=0, seen=None):
    if seen is None:
        seen = set()
    if depth > 40 or id(node) in seen:
        return
    seen.add(id(node))
    title = str(node.get_node_title()).replace("\n", " | ")
    lines.append(f"{'  '*depth}{node.get_name()} | {title}")
    then = node.find_output_pin("then")
    if then:
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
            if lp.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT:
                walk_from(lp.get_owning_node(), depth + 1, seen)

for node in ped.list_all_nodes():
    if node.get_class().get_name() != "K2Node_CustomEvent":
        continue
    if "PrimaryEquip" not in str(node.get_node_title()):
        continue
    lines.append("=== PrimaryEquip chain ===")
    walk_from(node)

# BP_Weapon_Pickup_Sniper SpawnPickup if exists
sniper_pickup = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Pickup_Sniper.BP_Weapon_Pickup_Sniper")
for g in unreal.BlueprintEditorLibrary.list_graphs(sniper_pickup):
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in ed.list_all_nodes():
        title = str(node.get_node_title())
        if any(k in title for k in ("Spawn", "Equip", "SetStaticMesh", "Optic", "Scope")):
            lines.append(f"[PickupSniper/{g.get_name()}] {node.get_name()} | {title.replace(chr(10),' | ')}")

OUT.write_text("\n".join(lines))
