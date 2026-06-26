"""Trace attachment struct after valid spawn."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_breakstruct11.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(bp)
)

for node in editor.list_all_nodes():
    if node.get_name() not in ("K2Node_BreakStruct_11", "K2Node_VariableGet_65"):
        continue
    lines.append(f"=== {node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')} ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        linked = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            owner = lp.get_owning_node()
            linked.append(f"{owner.get_name()}:{pname}")
        if linked:
            lines.append(f"  {pname} -> {linked}")

# walk from BreakStruct_11 sight pin consumers
for node in editor.list_all_nodes():
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        if "Sight" in pname and "688233" in pname:
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                owner = lp.get_owning_node()
                lines.append(
                    f"sight_pin_consumer {owner.get_name()} | "
                    f"{str(owner.get_node_title()).replace(chr(10),' | ')}"
                )

OUT.write_text("\n".join(lines))
