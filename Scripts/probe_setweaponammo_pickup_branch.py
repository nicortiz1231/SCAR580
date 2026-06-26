"""Trace SetWeaponAmmoData IsPickUp branch."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_setweaponammo_pickup_branch.log")
lines = []

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    if g.get_name() != "SetWeaponAmmoData":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        if node.get_class().get_name() != "K2Node_IfThenElse_1" and node.get_name() != "K2Node_IfThenElse_1":
            continue
        lines.append("=== Branch on IsPickUp ===")
        # true/false pins
        for branch in ("then", "else"):
            pin = node.find_output_pin(branch)
            if not pin:
                continue
            lines.append(f"  {branch}:")
            stack = [(pin, 2)]
            while stack:
                p, depth = stack.pop()
                if not p or depth > 30:
                    continue
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(p):
                    if lp.get_pin_direction() != unreal.EdGraphPinDirection.EGPD_INPUT:
                        continue
                    o = lp.get_owning_node()
                    lines.append(f"{'  '*depth}{o.get_name()} | {str(o.get_node_title()).replace(chr(10),' | ')}")
                    for nxt_name in ("then", "else"):
                        nxt = o.find_output_pin(nxt_name)
                        if nxt:
                            stack.append((nxt, depth + 1))

# pickup: what feeds SetWeaponAmmoData before call
pickup = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Pickup.BP_Item_Pickup")
ped = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(pickup))
lines.append("\n=== Pickup SetWeaponAmmoData node 18 wiring ===")
for node in ped.list_all_nodes():
    if node.get_name() != "K2Node_CallFunction_18":
        continue
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        linked = [f"{lp.get_owning_node().get_name()}:{unreal.BlueprintGraphPinLibrary.get_pin_name(lp)}" for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
        val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
        if linked or val:
            lines.append(f"  {pn} -> {linked or val}")

OUT.write_text("\n".join(lines))
