"""Probe UI_WeaponModding widget graphs for layout and combo population."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_weapon_modding_widget.log")
lines = []

wbp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Widgets/UI_WeaponModding.UI_WeaponModding")
if not wbp:
    raise RuntimeError("Missing UI_WeaponModding")

lines.append(f"widget={wbp}")

keywords = (
    "ComboBox", "Combo", "Option", "Enum", "Sight", "Laser", "Muzzle", "Grip",
    "Scale", "Render", "Orientation", "Portrait", "Landscape", "Slot", "Canvas",
    "Horizontal", "Vertical", "AddOption", "SetSelectedOption", "GenerateWidget",
)
for graph in unreal.BlueprintEditorLibrary.list_graphs(wbp):
    gname = graph.get_name()
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    hits = []
    for node in ed.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        cls = node.get_class().get_name()
        if any(k.lower() in title.lower() for k in keywords) or any(k.lower() in cls.lower() for k in keywords):
            hits.append(f"  {node.get_name()} | {cls} | {title}")
    if hits:
        lines.append(f"\n=== graph {gname} ({len(hits)} hits) ===")
        lines.extend(hits[:80])
        if len(hits) > 80:
            lines.append(f"  ... +{len(hits)-80} more")

# widget tree / designer props if exposed
for prop in ("widget_tree", "palette_category"):
    try:
        lines.append(f"{prop}={wbp.get_editor_property(prop)!r}")
    except Exception as exc:
        lines.append(f"{prop} ERR {exc}")

OUT.write_text("\n".join(lines))
