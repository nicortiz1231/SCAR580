"""Trace Break ST Attachments Sight pin consumers on character."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sight_breakstruct.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(bp))

for node in eg.list_all_nodes():
    if "Break ST Attachments" not in str(node.get_node_title()):
        continue
    lines.append(f"=== {node.get_name()} ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        if "Sight" not in pn and "sight" not in pn:
            continue
        links = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            o = lp.get_owning_node()
            links.append(f"{o.get_name()} | {str(o.get_node_title()).replace(chr(10), ' | ')}")
        lines.append(f"  {pn} -> {links}")

OUT.write_text("\n".join(lines))
