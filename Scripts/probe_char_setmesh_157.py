"""Check character SetStaticMesh 157/167 - might break sniper scope."""
import unreal
from pathlib import Path
OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_char_setmesh_157.log")
lines = []
char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
ced = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))
for name in ("K2Node_CallFunction_157", "K2Node_CallFunction_167", "K2Node_IfThenElse_7", "K2Node_IfThenElse_44"):
    for node in ced.list_all_nodes():
        if node.get_name() != name:
            continue
        lines.append(f"=== {name} | {node.get_node_title()} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            linked = [f"{lp.get_owning_node().get_name()}" for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            if linked or val:
                lines.append(f"  {pn} -> {linked or val}")
OUT.write_text("\n".join(lines))
