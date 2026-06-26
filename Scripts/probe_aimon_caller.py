"""Find who calls AIMOn function (56) vs CustomEvent (16) on SCAR."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_aimon_caller.log")
lines = []

char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))

for target in ("K2Node_CallFunction_56", "K2Node_CallFunction_379", "K2Node_CustomEvent_16", "K2Node_CustomEvent_19"):
    lines.append(f"\n=== Exec callers of {target} ===")
    for node in eg.list_all_nodes():
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) != unreal.EdGraphPinDirection.EGPD_OUTPUT:
                continue
            if str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin)) not in ("then", "Started", "Triggered", "Completed"):
                continue
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                if lp.get_owning_node().get_name() == target and lp.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT:
                    lines.append(f"  <- {node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')}")

OUT.write_text("\n".join(lines))
