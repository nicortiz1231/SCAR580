"""Probe Self node creation in widget blueprint."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_self_node.log")
lines = []

wbp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Widgets/UI_WeaponModding.UI_WeaponModding")
eg = unreal.BlueprintEditorLibrary.find_event_graph(wbp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)

for name in ("Self", "K2Node_Self", "GetSelf"):
    try:
        node = editor.create_node_from_name(name)
        lines.append(f"create_node_from_name({name!r}) -> {node} | {node.get_node_title() if node else None}")
    except Exception as exc:
        lines.append(f"create_node_from_name({name!r}) ERR {exc}")

# existing self-like nodes
for node in editor.list_all_nodes():
    title = str(node.get_node_title())
    cls = node.get_class().get_name()
    if cls == "K2Node_Self" or title == "Self":
        lines.append(f"existing {node.get_name()} | {title}")

OUT.write_text("\n".join(lines))
