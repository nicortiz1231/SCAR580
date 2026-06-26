"""Detailed weapon spawn chain probe."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_weapons_gone_v2.log")
lines = []


def pin_info(node):
    lines.append(f"--- {node.get_name()} | {str(node.get_node_title()).replace(chr(10), ' | ')} ---")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        linked = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            o = lp.get_owning_node()
            linked.append(f"{o.get_name()}:{str(unreal.BlueprintGraphPinLibrary.get_pin_name(lp))}")
        val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
        extra = f" val={val}" if val else ""
        lines.append(f"  {pname} -> {linked or 'NONE'}{extra}")


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(bp)
)

for name in (
    "K2Node_MacroInstance_4",
    "K2Node_CallFunction_234",
    "K2Node_CallFunction_212",
    "K2Node_CallFunction_140",
    "K2Node_CallFunction_141",
    "K2Node_VariableGet_133",
    "K2Node_VariableGet_83",
    "K2Node_VariableSet_0",
    "K2Node_VariableSet_59",
    "K2Node_VariableSet_19",
    "K2Node_VariableSet_15",
):
    for node in editor.list_all_nodes():
        if node.get_name() == name:
            pin_info(node)

OUT.write_text("\n".join(lines))
