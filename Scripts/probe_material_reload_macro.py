"""Inspect Material Reload macro used by AutomaticBase."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_material_reload_macro.log")
lines = []

# Macro graphs live on the weapon BP or as macro assets
bp = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase"
)
for graph in unreal.BlueprintEditorLibrary.list_graphs(bp):
    gname = graph.get_name()
    if "Material Reload" not in gname and "Macro" not in gname:
        continue
    lines.append(f"\n=== graph {gname} ===")
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    for node in ed.list_all_nodes():
        lines.append(f"  {node.get_name()} | {str(node.get_node_title()).replace(chr(10), ' ')}")

# Dump macro instance connections from EventGraph reload section
eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(eg)
for node in ed.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " ")
    if "Material Reload" not in title and "LaserMesh" not in title and "Event Reload" not in title:
        continue
    lines.append(f"\nNODE {node.get_name()} | {title}")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        for cpin in pin.list_connected_pins():
            cnode = cpin.get_owning_node()
            lines.append(f"  {pname} <-> {cnode.get_name()} | {str(cnode.get_node_title()).replace(chr(10), ' ')}")

OUT.write_text("\n".join(lines))
