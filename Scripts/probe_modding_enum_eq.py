"""Trace EnumEquality_9 and modding exec gap."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_modding_enum_eq.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(bp))

for node in eg.list_all_nodes():
    if node.get_name() in ("K2Node_EnumEquality_9", "K2Node_IfThenElse_28", "K2Node_IfThenElse_26"):
        lines.append(f"\n=== {node.get_name()} | {node.get_node_title()} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            linked = [f"{lp.get_owning_node().get_name()}:{str(unreal.BlueprintGraphPinLibrary.get_pin_name(lp))}" for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
            if linked:
                lines.append(f"  {pn} -> {linked}")

# find what should feed VariableGet_144 execute - search nearby comments
for node in eg.list_all_nodes():
    if "Modding" in str(node.get_node_title()) or node.get_name() in ("K2Node_Knot_8", "K2Node_Knot_9"):
        lines.append(f"NODE {node.get_name()} | {node.get_node_title()}")

OUT.write_text("\n".join(lines))
