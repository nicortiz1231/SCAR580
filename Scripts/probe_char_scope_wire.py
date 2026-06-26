"""Verify character scope wiring after fix attempt."""
import unreal
from pathlib import Path
OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_char_scope_wire.log")
lines = []
char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
ced = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))
for node in ced.list_all_nodes():
    if node.get_name() != "K2Node_CallFunction_141":
        continue
    lines.append("=== SpawnAttachments 141 ===")
    then = node.find_output_pin("then")
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
        o = lp.get_owning_node()
        lines.append(f"  then -> {o.get_name()} | {o.get_node_title()}")
        t2 = o.find_output_pin("then")
        if t2:
            for lp2 in unreal.BlueprintGraphPinLibrary.list_connected_pins(t2):
                o2 = lp2.get_owning_node()
                lines.append(f"    then -> {o2.get_name()} | {o2.get_node_title()}")
for node in ced.list_all_nodes():
    if "SetStaticMesh" not in str(node.get_node_title()):
        continue
    lines.append(f"SetStaticMesh node {node.get_name()}")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        if pn in ("self", "NewMesh", "execute"):
            linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            if linked or val:
                lines.append(f"  {pn} -> {linked or val}")
OUT.write_text("\n".join(lines))
