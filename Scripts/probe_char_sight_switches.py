"""Full character ENUM_Sights switch branch dump."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_char_sight_switches.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(bp))

for node in eg.list_all_nodes():
    if "Switch on ENUM_Sights" not in str(node.get_node_title()):
        continue
    lines.append(f"=== {node.get_name()} ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        if not (pn.startswith("NewEnumerator") or pn == "Default"):
            continue
        links = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            o = lp.get_owning_node()
            links.append(f"{o.get_name()} | {str(o.get_node_title()).replace(chr(10), ' | ')}")
        lines.append(f"  {pn} -> {links if links else 'UNCONNECTED'}")

# trace what feeds Selection pin
for node in eg.list_all_nodes():
    if "Switch on ENUM_Sights" not in str(node.get_node_title()):
        continue
    sel = node.find_input_pin("Selection")
    if not sel:
        continue
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(sel):
        o = lp.get_owning_node()
        lines.append(f"Selection source: {o.get_name()} | {str(o.get_node_title()).replace(chr(10), ' | ')}")

OUT.write_text("\n".join(lines))
