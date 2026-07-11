"""Trace LaserMesh SetStaticMesh in AutomaticBase and SpawnAttachments flow."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_laser_mesh_static.log")
lines = []

bp = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase"
)

def pin_default(pin):
    try:
        return pin.get_default_value()
    except Exception:
        return ""

for graph in unreal.BlueprintEditorLibrary.list_graphs(bp):
    gname = graph.get_name()
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    for node in ed.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " ")
        if "LaserMesh" in title or ("SetStaticMesh" in title and any(
            "LaserMesh" in str(unreal.BlueprintGraphPinLibrary.get_pin_name(p))
            for p in unreal.BlueprintEditorLibrary.list_all_pins(node)
        )):
            lines.append(f"\n[{gname}] {node.get_name()} | {title}")
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                default = pin_default(pin)
                conns = []
                for cpin in pin.list_connected_pins():
                    cn = cpin.get_owning_node()
                    conns.append(f"{cn.get_name()}|{str(cn.get_node_title()).replace(chr(10),' ')}.{unreal.BlueprintGraphPinLibrary.get_pin_name(cpin)}")
                if default or conns:
                    lines.append(f"  {pname} default={default!r} -> {conns}")

# Also find SpawnAttachments function graph by name substring
for graph in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if "SpawnAttachment" not in graph.get_name():
        continue
    lines.append(f"\n=== SPAWN GRAPH {graph.get_name()} ===")
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    for node in ed.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " ")
        if any(k in title for k in ("Laser", "Flash", "Spawn", "Switch", "Mesh", "Toggle")):
            lines.append(f"  {node.get_name()} | {title}")

# EventGraph nodes with SpawnAttachments in title
eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(eg)
for node in ed.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " ")
    if "SpawnAttachments" in title or "SpawnActor BP Laser" in title or "Switch on ENUM_Laser" in title:
        lines.append(f"\n[EventGraph] {node.get_name()} | {title}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            for cpin in pin.list_connected_pins():
                cn = cpin.get_owning_node()
                ct = str(cn.get_node_title()).replace("\n", " ")
                if any(k in ct for k in ("Laser", "Flash", "Mesh", "Toggle", "Spawn")):
                    lines.append(f"  {pname} -> {cn.get_name()} | {ct}")

OUT.write_text("\n".join(lines))
