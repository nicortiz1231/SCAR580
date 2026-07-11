"""Trace Construct Sequence and AddOption targets."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_modding_sequence.log")
lines = []

wbp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Widgets/UI_WeaponModding.UI_WeaponModding")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(wbp))

seq = next(n for n in eg.list_all_nodes() if n.get_name() == "K2Node_ExecutionSequence_0")
lines.append(f"Sequence {seq.get_node_title()}")
for pin in unreal.BlueprintEditorLibrary.list_all_pins(seq):
    pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
    if not pn.startswith("then"):
        continue
    linked = []
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
        owner = lp.get_owning_node()
        linked.append(f"{owner.get_name()} | {owner.get_node_title()}")
    lines.append(f"  {pn} -> {linked}")

lines.append("\n=== AddOption nodes ===")
for node in eg.list_all_nodes():
    if "AddOption" not in str(node.get_node_title()):
        continue
    lines.append(f"\n{node.get_name()} | {node.get_node_title()}")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        if pn in ("execute", "self", "Option"):
            linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            lines.append(f"  {pn} default={val!r} linked={linked}")

lines.append("\n=== SetSelectedIndex on comboboxes ===")
for node in eg.list_all_nodes():
    if "SetSelectedIndex" not in str(node.get_node_title()):
        continue
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        if str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin)) == "self":
            linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
            if linked:
                lines.append(f"  {node.get_name()} self -> {linked}")

OUT.write_text("\n".join(lines))
