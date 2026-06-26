"""Probe CallFunction_56 downstream and IfThenElse_29."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_cf56.log")
lines = []

char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))

for name in ("K2Node_CallFunction_56", "K2Node_VariableSet_27", "K2Node_VariableSet_49", "K2Node_IfThenElse_29", "K2Node_IfThenElse_9"):
    for node in eg.list_all_nodes():
        if node.get_name() != name:
            continue
        lines.append(f"\n=== {name} | {str(node.get_node_title()).replace(chr(10),' | ')} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
            if linked:
                lines.append(f"  {pn} linked={linked}")

OUT.write_text("\n".join(lines))
