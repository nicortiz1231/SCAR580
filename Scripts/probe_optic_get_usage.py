"""What uses OpticSight getters 221/226 on sniper spawn path?"""
import unreal
from pathlib import Path
OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_optic_get_usage.log")
lines = []
char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
ced = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))
for name in ("K2Node_VariableGet_221", "K2Node_VariableGet_226", "K2Node_VariableGet_83", "K2Node_VariableGet_192"):
    for node in ced.list_all_nodes():
        if node.get_name() != name:
            continue
        lines.append(f"=== {name} | {node.get_node_title()} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            linked = [f"{lp.get_owning_node().get_name()}:{pn}" for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
            if linked:
                lines.append(f"  {pn} -> {linked}")
OUT.write_text("\n".join(lines))
