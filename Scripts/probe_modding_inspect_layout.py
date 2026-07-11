"""Find INSPECT text + layout widgets in UI_WeaponModding."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_modding_inspect_layout.log")
lines = []

WBP = "/Game/BodycamFPSKIT/Blueprints/Widgets/UI_WeaponModding.UI_WeaponModding"
wbp = unreal.load_asset(f"{WBP}.UI_WeaponModding")

# graph nodes mentioning inspect / text / press
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(wbp))
lines.append("=== EventGraph hits ===")
for node in eg.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    if any(k in title.upper() for k in ("INSPECT", "PRESS", "TEXT", "Z")):
        lines.append(f"  {node.get_name()} | {title}")

for graph in unreal.BlueprintEditorLibrary.list_graphs(wbp):
    gname = graph.get_name()
    if gname == "EventGraph":
        continue
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    hits = []
    for node in ed.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if any(k in title.upper() for k in ("INSPECT", "PRESS", "TEXT", "HORIZONTAL", "CANVAS", "OVERLAY", "BOX")):
            hits.append(f"  {node.get_name()} | {title}")
    if hits:
        lines.append(f"\n=== graph {gname} ===")
        lines.extend(hits[:60])

# widget bindings via variable gets across all graphs
lines.append("\n=== widget binding names (Get *) ===")
names = set()
for graph in unreal.BlueprintEditorLibrary.list_graphs(wbp):
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    for node in ed.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if title.startswith("Get "):
            names.add(title[4:])
for n in sorted(names):
    if any(k in n.upper() for k in ("INSPECT", "TEXT", "PRESS", "HINT", "PROMPT", "BOX", "CANVAS", "HORIZONTAL", "VERTICAL", "OVERLAY")):
        lines.append(f"  {n}")

# try WidgetTree via generated class CDO subobjects
cls = wbp.generated_class()
for obj in unreal.get_objects_of_class(cls):
    name = obj.get_name()
    if any(k in name.upper() for k in ("INSPECT", "TEXT", "PRESS", "HINT")):
        lines.append(f"OBJ {name} {obj.get_class().get_name()}")

OUT.write_text("\n".join(lines))
