"""Inspect current scope wiring after spawn att on character."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_char_scope_wiring.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(bp))

for name in ("K2Node_CallFunction_140", "K2Node_CallFunction_141"):
    for node in eg.list_all_nodes():
        if node.get_name() != name:
            continue
        lines.append(f"=== {name} ===")
        then = node.find_output_pin("then")
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
            o = lp.get_owning_node()
            lines.append(f"  then -> {o.get_name()} | {str(o.get_node_title()).replace(chr(10), ' | ')}")
            then2 = o.find_output_pin("then")
            if then2:
                for lp2 in unreal.BlueprintGraphPinLibrary.list_connected_pins(then2):
                    o2 = lp2.get_owning_node()
                    lines.append(f"    then -> {o2.get_name()} | {str(o2.get_node_title()).replace(chr(10), ' | ')}")

OUT.write_text("\n".join(lines))
