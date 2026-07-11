"""Trace UI_WeaponModding laser selection changed exec chain."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_ui_laser_change.log")
lines = []

wbp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Widgets/UI_WeaponModding.UI_WeaponModding")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(wbp))

start = next(n for n in eg.list_all_nodes() if "On Selection Changed (Laser)" in str(n.get_node_title()))

def walk(node, depth=0, seen=None):
    if seen is None:
        seen = set()
    if depth > 30 or node.get_name() in seen:
        return
    seen.add(node.get_name())
    lines.append(f"{'  '*depth}{node.get_name()} | {node.get_node_title()}")
    then = node.find_output_pin("then")
    if not then:
        return
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
        if lp.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT:
            walk(lp.get_owning_node(), depth + 1, seen)

lines.append("=== Laser selection changed chain ===")
walk(start)
OUT.write_text("\n".join(lines))
