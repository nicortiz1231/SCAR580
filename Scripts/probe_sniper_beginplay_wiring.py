"""Verify sniper BeginPlay scope pin wiring + OpticSight component."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sniper_beginplay_wiring.log")
lines = []

sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(sniper))

for node in eg.list_all_nodes():
    lines.append(f"{node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')}")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        linked = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            o = lp.get_owning_node()
            linked.append(f"{o.get_name()}:{pn}")
        val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
        if linked or val:
            lines.append(f"  {pn} -> {linked or val}")

# component template via SCS
bp_class = sniper.generated_class()
cdo = unreal.get_default_object(bp_class)
comps = cdo.get_components_by_class(unreal.StaticMeshComponent)
for c in comps:
    if "OpticSight" in c.get_name():
        sm = c.get_static_mesh()
        lines.append(f"runtime CDO OpticSight mesh={sm.get_path_name() if sm else None} hidden={c.is_hidden_in_game()}")

# BP_Item_Pickup flow
pickup_base = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Pickup.BP_Item_Pickup")
if pickup_base:
    peg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(pickup_base))
    lines.append("=== BP_Item_Pickup EventGraph key nodes ===")
    for node in peg.list_all_nodes():
        t = str(node.get_node_title()).replace("\n", " | ")
        if any(k in t for k in ("Overlap", "Pickup", "ItemData", "Equip", "Add", "Spawn", "SetWeapon")):
            lines.append(f"  {node.get_name()} | {t}")

OUT.write_text("\n".join(lines))
