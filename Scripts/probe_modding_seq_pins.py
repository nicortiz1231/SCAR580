"""Inspect Sequence pin wiring and IfThenElse after Construct."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_modding_seq_pins.log")
lines = []

wbp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Widgets/UI_WeaponModding.UI_WeaponModding")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(wbp))

for node in eg.list_all_nodes():
    name = node.get_name()
    if name not in (
        "K2Node_ExecutionSequence_0",
        "K2Node_IfThenElse_3",
        "K2Node_Knot_9",
        "K2Node_Event_3",
        "K2Node_Event_0",
    ):
        continue
    lines.append(f"\n{node.get_name()} | {node.get_node_title()}")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        linked = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            owner = lp.get_owning_node()
            linked.append(f"{owner.get_name()}:{str(unreal.BlueprintGraphPinLibrary.get_pin_name(lp))}")
        if linked or pn in ("execute", "then", "else", "Condition") or pn.startswith("then_"):
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            lines.append(f"  {pn} default={val!r} -> {linked}")

# upstream into sequence
seq = next(n for n in eg.list_all_nodes() if n.get_name() == "K2Node_ExecutionSequence_0")
lines.append("\n=== exec into Sequence ===")
exec_in = seq.find_input_pin("execute")
if exec_in:
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(exec_in):
        owner = lp.get_owning_node()
        lines.append(f"  from {owner.get_name()} | {owner.get_node_title()} pin {unreal.BlueprintGraphPinLibrary.get_pin_name(lp)}")

OUT.write_text("\n".join(lines))
