"""Find aim/reload visibility branches for laser on weapon bases."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_laser_aim_visibility.log")
lines = []

for path in (
    "/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base",
    "/Game/BodycamFPSKIT/Blueprints/Attachments/Laser/Blueprints/BP_Laser",
):
    name = path.split("/")[-1]
    bp = unreal.load_asset(f"{path}.{name}")
    lines.append(f"\n######## {name} ########")
    if not bp:
        lines.append("MISSING")
        continue
    for graph in unreal.BlueprintEditorLibrary.list_graphs(bp):
        gname = graph.get_name()
        if gname not in ("EventGraph", "AimDownSight", "ToggleLaser", "OnRep_LaserActive"):
            continue
        ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        lines.append(f"\n--- graph {gname} ---")
        for node in ed.list_all_nodes():
            title = str(node.get_node_title())
            if any(
                k in title
                for k in (
                    "IsAim",
                    "Reload",
                    "Laser",
                    "Flash",
                    "Visibility",
                    "Hidden",
                    "LaserActive",
                    "LaserRef",
                    "LaserBeam",
                    "LaserDot",
                    "UseIR",
                    "Aim",
                )
            ):
                lines.append(f"  {node.get_name()} | {title}")

OUT.write_text("\n".join(lines))
unreal.log(f"[probe_laser_aim_visibility] wrote {OUT}")
