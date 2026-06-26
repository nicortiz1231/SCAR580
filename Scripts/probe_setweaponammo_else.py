"""Trace SetWeaponAmmoData IsPickUp=false (else) branch."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_setweaponammo_else.log")
lines = []

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
g = next(g for g in unreal.BlueprintEditorLibrary.list_graphs(item) if g.get_name() == "SetWeaponAmmoData")
ed = unreal.BlueprintGraphEditor.get_graph_editor(g)

branch = next(n for n in ed.list_all_nodes() if n.get_name() == "K2Node_IfThenElse_1")
else_pin = branch.find_output_pin("else")
then_pin = branch.find_output_pin("then")

def walk(pin, label, depth=0, seen=None):
    if seen is None:
        seen = set()
    lines.append(f"--- {label} ---")
    stack = [(pin, depth)]
    while stack:
        p, d = stack.pop()
        if not p or d > 25:
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(p):
            if lp.get_pin_direction() != unreal.EdGraphPinDirection.EGPD_INPUT:
                continue
            o = lp.get_owning_node()
            if id(o) in seen:
                continue
            seen.add(id(o))
            t = str(o.get_node_title()).replace("\n", " | ")
            lines.append(f"{'  '*d}{o.get_name()} | {t}")
            if "Set ItemData" in t or "ItemData" in t:
                for pin in unreal.BlueprintEditorLibrary.list_all_pins(o):
                    pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                    if "ItemData" in pn:
                        linked = [lp2.get_owning_node().get_name() for lp2 in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
                        val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                        if linked or val:
                            lines.append(f"{'  '*(d+1)}{pn} -> {linked or val}")
            for branch in ("then", "else"):
                nxt = o.find_output_pin(branch)
                if nxt:
                    stack.append((nxt, d + 1))

walk(then_pin, "IsPickUp TRUE (then)")
walk(else_pin, "IsPickUp FALSE (else)")

OUT.write_text("\n".join(lines))
