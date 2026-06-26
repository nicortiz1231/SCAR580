"""Trace FOV call chain from sniper scope to SetFieldOfView."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_fov_chain.log")
lines = []

char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))

# Trace from CallFunction_193
start = None
for node in eg.list_all_nodes():
    if node.get_name() == "K2Node_CallFunction_193":
        start = node
        break

if start:
    lines.append("=== Chain from K2Node_CallFunction_193 (sniper scope FOV) ===")
    # FOV is a call to custom event - find K2Node_CallFunction_27 or similar
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(start):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            o = lp.get_owning_node()
            lines.append(f"  {pn} -> {o.get_name()} | {str(o.get_node_title()).replace(chr(10),' | ')}")

# Full dump of nodes 27, 296, 40, Select_5, CustomEvent_71
for name in ("K2Node_CallFunction_27", "K2Node_CallFunction_296", "K2Node_CallFunction_40", "K2Node_Select_5", "K2Node_CustomEvent_71"):
    for node in eg.list_all_nodes():
        if node.get_name() != name:
            continue
        lines.append(f"\n=== {name} | {str(node.get_node_title()).replace(chr(10),' | ')} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
            if val or linked or pn.startswith("NewEnumerator"):
                lines.append(f"  {pn} val={val!r} linked={linked}")

# Who else uses NewEnumerator14 as TargetFOV?
lines.append("\n=== All nodes with TargetFOV=NewEnumerator14 ===")
for node in eg.list_all_nodes():
    pin = node.find_input_pin("TargetFOV")
    if not pin:
        continue
    val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
    if val == "NewEnumerator14":
        lines.append(f"  {node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')}")

OUT.write_text("\n".join(lines))
