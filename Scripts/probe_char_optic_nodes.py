"""Probe character OpticSight Get nodes 219-226 and sight mesh apply."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_char_optic_nodes.log")
lines = []

char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))

for name in (
    "K2Node_VariableGet_219", "K2Node_VariableGet_221", "K2Node_VariableGet_224", "K2Node_VariableGet_226",
    "K2Node_SwitchEnum_3", "K2Node_SwitchEnum_4", "K2Node_IfThenElse_17", "K2Node_CallFunction_193",
    "K2Node_CallFunction_43", "K2Node_CallFunction_44",
):
    for node in editor.list_all_nodes():
        if node.get_name() != name:
            continue
        title = str(node.get_node_title()).replace("\n", " | ")
        lines.append(f"=== {name} | {title} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            linked = [f"{lp.get_owning_node().get_name()}:{unreal.BlueprintGraphPinLibrary.get_pin_name(lp)}" for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            if linked or (val and pn not in ("execute",)):
                lines.append(f"  {pn} -> {linked or val}")

# any SetStaticMesh on char event graph
lines.append("\n=== ALL SetStaticMesh on char EventGraph ===")
for node in editor.list_all_nodes():
    if "SetStaticMesh" not in str(node.get_node_title()):
        continue
    lines.append(f"{node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')}")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        if pn in ("execute", "then", "self", "NewMesh"):
            linked = [f"{lp.get_owning_node().get_name()}" for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            if linked or val:
                lines.append(f"  {pn} -> {linked or val}")

OUT.write_text("\n".join(lines))
