"""Inspect SpawnAttachments laser branch on AutomaticBase."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_spawn_attachments_laser.log")
lines = []

bp = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase"
)
for fname in ("SpawnAttachments", "ToggleLaser", "ToggleFlashlight", "AimDownSight"):
    graph = None
    for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
        if g.get_name() == fname:
            graph = g
            break
    lines.append(f"\n######## {fname} graph={graph is not None} ########")
    if not graph:
        continue
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    for node in ed.list_all_nodes():
        title = node.get_node_title()
        if any(k in title for k in ("Laser", "Flash", "Visibility", "Spawn", "Switch", "Toggle", "Aim", "Mesh")):
            lines.append(f"  {node.get_name()} | {title}")

laser_bp = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Attachments/Laser/Blueprints/BP_Laser.BP_Laser"
)
cdo = unreal.get_default_object(laser_bp.generated_class())
for prop in ("LaserActive", "UseIRLaser"):
    try:
        lines.append(f"BP_Laser CDO {prop}={cdo.get_editor_property(prop)}")
    except Exception as e:
        lines.append(f"BP_Laser CDO {prop} ERR {e}")

OUT.write_text("\n".join(lines))
