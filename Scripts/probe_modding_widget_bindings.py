"""Find widget binding names in UI_WeaponModding graph."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_modding_widget_bindings.log")
lines = []

wbp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Widgets/UI_WeaponModding.UI_WeaponModding")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(wbp))

widget_names = set()
for node in eg.list_all_nodes():
    cls = node.get_class().get_name()
    title = str(node.get_node_title()).replace("\n", " | ")
    if cls == "K2Node_VariableGet" and title.startswith("Get "):
        widget_names.add(title.replace("Get ", ""))

lines.append("VariableGet widget bindings:")
for name in sorted(widget_names):
    lines.append(f"  {name}")

# also scan all graphs
for graph in unreal.BlueprintEditorLibrary.list_graphs(wbp):
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    for node in ed.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if title.startswith("Get ") and any(k in title for k in ("Sight", "Laser", "Muzzle", "GRIP", "Box", "Canvas", "Text", "Inspect", "Horizontal", "Vertical", "Overlay")):
            lines.append(f"{graph.get_name()}: {node.get_name()} | {title}")

OUT.write_text("\n".join(lines))
