"""Dump AimDownSight and Reload laser spawn sections."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_aimdown_laser.log")
lines = []

bp = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase"
)
for fname in ("AimDownSight", "EventGraph"):
    graph = None
    for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
        if g.get_name() == fname:
            graph = g
            break
    lines.append(f"\n######## {fname} ########")
    if not graph:
        lines.append("missing")
        continue
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    for node in ed.list_all_nodes():
        title = str(node.get_node_title())
        if fname == "AimDownSight" or any(
            k in title for k in ("Laser", "Reload", "SpawnActor", "LaserRef", "Toggle", "Visibility", "IsAim")
        ):
            lines.append(f"  {node.get_name()} | {title}")

OUT.write_text("\n".join(lines))
unreal.log(f"[probe_aimdown_laser] wrote {OUT}")
