"""Find Tick/Aim/Animation nodes affecting laser on weapon + BP_Laser trace visibility."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_laser_aim_tick.log")
lines = []

for path in (
    "/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase",
    "/Game/BodycamFPSKIT/Blueprints/Attachments/Laser/Blueprints/BP_Laser",
):
    name = path.split("/")[-1]
    bp = unreal.load_asset(f"{path}.{name}")
    lines.append(f"\n======== {name} ========")
    for graph in unreal.BlueprintEditorLibrary.list_graphs(bp):
        gname = graph.get_name()
        ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        for node in ed.list_all_nodes():
            title = str(node.get_node_title()).replace("\n", " ")
            upper = title.upper()
            if not any(k in upper for k in ("TICK", "AIM", "LASER", "FLASH", "VISIB", "HIDDEN", "RELOAD", "ANIM")):
                continue
            if gname in ("EventGraph", "LaserDotTrace", "OnRep_LaserActive", "ToggleFlashlight", "ToggleLaser"):
                lines.append(f"  [{gname}] {node.get_name()} | {title}")

OUT.write_text("\n".join(lines))
