"""Probe K2Node_CustomEvent editable properties."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_custom_event_props.log")
lines = []

sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(sniper))
for node in eg.list_all_nodes():
    if node.get_class().get_name() != "K2Node_CustomEvent":
        continue
    lines.append(f"node={node.get_name()} title={node.get_node_title()}")
    for prop in sorted(dir(node)):
        if prop.startswith("_"):
            continue
        try:
            val = node.get_editor_property(prop)
            if val not in (None, "", False, 0):
                lines.append(f"  {prop}={val!r}")
        except Exception:
            pass

# item base SpawnAttachments event props
item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
ieg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(item))
for node in ieg.list_all_nodes():
    if node.get_name() != "K2Node_CustomEvent_3":
        continue
    lines.append(f"item node title={node.get_node_title()}")
    for prop in sorted(dir(node)):
        if prop.startswith("_"):
            continue
        try:
            val = node.get_editor_property(prop)
            if val not in (None, "", False, 0):
                lines.append(f"  item.{prop}={val!r}")
        except Exception:
            pass

OUT.write_text("\n".join(lines))
