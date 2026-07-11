"""Dump all widget bindings referenced in UI_WeaponModding."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_modding_all_bindings.log")
lines = []

wbp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Widgets/UI_WeaponModding.UI_WeaponModding")
names = set()
for graph in unreal.BlueprintEditorLibrary.list_graphs(wbp):
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    for node in ed.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if title.startswith("Get "):
            names.add(title[4:])

lines.append("ALL GET bindings:")
for n in sorted(names):
    lines.append(f"  {n}")

# search string literals in graph default values
lines.append("\n=== pin values containing inspect/press ===")
for graph in unreal.BlueprintEditorLibrary.list_graphs(wbp):
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    for node in ed.list_all_nodes():
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            val = str(unreal.BlueprintGraphPinLibrary.get_pin_value(pin))
            if val and any(k in val.upper() for k in ("INSPECT", "PRESS", "FOR INSPECT")):
                lines.append(f"{graph.get_name()} {node.get_name()} | {node.get_node_title()} pin={unreal.BlueprintGraphPinLibrary.get_pin_name(pin)} val={val}")

OUT.write_text("\n".join(lines))
