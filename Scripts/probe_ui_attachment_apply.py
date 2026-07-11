"""Trace shared attachment selection branch in modding UI."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_ui_attachment_apply.log")
lines = []

wbp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Widgets/UI_WeaponModding.UI_WeaponModding")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(wbp))
branch = next(n for n in eg.list_all_nodes() if n.get_name() == "K2Node_IfThenElse_0")

def walk(node, depth=0, seen=None):
    if seen is None:
        seen = set()
    if depth > 35 or node.get_name() in seen:
        return
    seen.add(node.get_name())
    lines.append(f"{'  '*depth}{node.get_name()} | {node.get_node_title()}")
    then = node.find_output_pin("then")
    else_pin = node.find_output_pin("else")
    for pin in (then, else_pin):
        if not pin:
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            if lp.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT:
                walk(lp.get_owning_node(), depth + 1, seen)

lines.append("=== IfThenElse_0 then branch ===")
walk(branch)
OUT.write_text("\n".join(lines))
