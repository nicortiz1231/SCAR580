"""Probe AIMOn/AIMOff exec chains on SCAR character."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_aimon_chain.log")
lines = []

char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))

def walk_forward(start_pin, depth=0, seen=None):
    if not start_pin or depth > 18:
        return
    if seen is None:
        seen = set()
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(start_pin):
        if lp.get_pin_direction() != unreal.EdGraphPinDirection.EGPD_INPUT:
            continue
        o = lp.get_owning_node()
        nid = o.get_name()
        if nid in seen:
            continue
        seen.add(nid)
        lines.append(f"{'  '*depth}{nid} | {str(o.get_node_title()).replace(chr(10),' | ')}")
        then = o.find_output_pin("then")
        if then:
            walk_forward(then, depth + 1, seen)

for name in ("K2Node_CustomEvent_16", "K2Node_CustomEvent_19", "K2Node_CallFunction_56", "K2Node_CallFunction_379"):
    for node in eg.list_all_nodes():
        if node.get_name() != name:
            continue
        lines.append(f"\n=== Forward from {name} ===")
        then = node.find_output_pin("then")
        walk_forward(then)

for vname in ("K2Node_VariableGet_81", "K2Node_VariableGet_191"):
    for node in eg.list_all_nodes():
        if node.get_name() != vname:
            continue
        lines.append(f"\n=== {vname} all pins ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
            lines.append(f"  {pn} linked={linked}")

OUT.write_text("\n".join(lines))
