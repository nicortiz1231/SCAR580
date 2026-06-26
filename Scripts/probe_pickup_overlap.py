"""Trace item BeginPlay and pickup overlap for ItemData + scope."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_pickup_overlap.log")
lines = []

pickup = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Pickup_Sniper.BP_Weapon_Pickup_Sniper")
for g in unreal.BlueprintEditorLibrary.list_graphs(pickup):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if any(k in title for k in ("Overlap", "Pickup", "ItemData", "Equip", "Spawn", "SetWeapon")):
            lines.append(f"[{g.get_name()}] {node.get_name()} | {title}")

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
ied = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(item))
lines.append("=== item BeginPlay chain ===")
for node in ied.list_all_nodes():
    if node.get_name() != "K2Node_Event_0":
        continue
    stack = [(node.find_output_pin("then"), 0)]
    while stack:
        pin, depth = stack.pop()
        if not pin or depth > 15:
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            if lp.get_pin_direction() != unreal.EdGraphPinDirection.EGPD_INPUT:
                continue
            o = lp.get_owning_node()
            lines.append(f"{'  '*depth}{o.get_name()} | {str(o.get_node_title()).replace(chr(10),' | ')}")
            nxt = o.find_output_pin("then")
            if nxt:
                stack.append((nxt, depth + 1))

cdo = unreal.get_default_object(item.generated_class())
try:
    lines.append(f"item default ItemData={cdo.get_editor_property('ItemData')!r}")
except Exception as exc:
    lines.append(f"ItemData ERR {exc}")

OUT.write_text("\n".join(lines))
