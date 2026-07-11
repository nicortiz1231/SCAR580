"""Dump SetVisibility and laser-related nodes in AutomaticBase EventGraph."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_automatic_visibility.log")
lines = []

bp = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase"
)
graph = None
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if g.get_name() == "EventGraph":
        graph = g
        break

if not graph:
    lines.append("EventGraph not found")
else:
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    for node in ed.list_all_nodes():
        title = node.get_node_title()
        if "SetVisibility" in title or "Set Hidden" in title or "Hidden in Game" in title:
            lines.append(f"\nNODE {node.get_name()} | {title}")
            try:
                pins = node.get_pins()
                for pin in pins:
                    lines.append(f"  PIN {pin.get_name()} dir={pin.get_direction()} default={pin.get_default_value()}")
            except Exception as e:
                lines.append(f"  pins err {e}")

OUT.write_text("\n".join(lines))
