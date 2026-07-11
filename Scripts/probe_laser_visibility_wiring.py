"""Trace laser SetVisibility wiring in weapon bases and BP_Laser."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_laser_visibility_wiring.log")
lines = []

WEAPONS = [
    "/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base",
]

for base in WEAPONS:
    name = base.split("/")[-1]
    bp = unreal.load_asset(f"{base}.{name}")
    if not bp:
        lines.append(f"MISSING {base}")
        continue
    lines.append(f"\n======== {name} ========")
    for graph in unreal.BlueprintEditorLibrary.list_graphs(bp):
        gname = graph.get_name()
        if gname not in ("EventGraph", "UserConstructionScript"):
            continue
        ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        for node in ed.list_all_nodes():
            title = str(node.get_node_title()).replace("\n", " ")
            if "SetVisibility" not in title and "Set Hidden in Game" not in title:
                continue
            lines.append(f"\n  [{gname}] {node.get_name()} | {title}")
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                pdir = unreal.BlueprintGraphPinLibrary.get_pin_direction(pin)
                default = pin.get_default_value() if hasattr(pin, "get_default_value") else ""
                conns = []
                for cpin in pin.list_connected_pins():
                    cnode = cpin.get_owning_node()
                    ctitle = str(cnode.get_node_title()).replace("\n", " ") if cnode else "?"
                    cpname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(cpin))
                    conns.append(f"{cnode.get_name()}({ctitle}).{cpname}")
                if conns or default:
                    lines.append(f"    {pname} [{pdir}] default={default!r} -> {conns}")

# BP_Laser EventGraph visibility
laser = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Attachments/Laser/Blueprints/BP_Laser.BP_Laser")
lines.append("\n======== BP_Laser ========")
for graph in unreal.BlueprintEditorLibrary.list_graphs(laser):
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    for node in ed.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " ")
        if any(k in title for k in ("SetVisibility", "LaserActive", "LaserBeam", "LaserDot", "Flashlight")):
            lines.append(f"  [{graph.get_name()}] {node.get_name()} | {title}")

OUT.write_text("\n".join(lines))
