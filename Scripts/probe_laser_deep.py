"""Dump BP_Laser + AutomaticBase laser-related graphs."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_laser_deep.log")
lines = []

for path, label in (
    ("/Game/BodycamFPSKIT/Blueprints/Attachments/Laser/Blueprints/BP_Laser", "BP_Laser"),
    ("/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase", "AutomaticBase"),
):
    bp = unreal.load_asset(f"{path}.{path.split('/')[-1]}")
    lines.append(f"\n######## {label} ########")
    for graph in unreal.BlueprintEditorLibrary.list_graphs(bp):
        gname = graph.get_name()
        if not any(k in gname for k in ("ToggleLaser", "ToggleFlashlight", "EventGraph", "Laser")):
            continue
        ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        hits = []
        for node in ed.list_all_nodes():
            title = str(node.get_node_title()).replace("\n", " | ")
            if any(k in title.upper() for k in ("LASER", "FLASH", "VISIB", "AIM", "RELOAD", "ACTIVE", "TICK", "TRACE", "DECAL", "BEAM")):
                hits.append(f"  {node.get_name()} | {title}")
        if hits:
            lines.append(f"\n--- graph {gname} ---")
            lines.extend(hits[:60])

# BP_Laser CDO props
laser = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Attachments/Laser/Blueprints/BP_Laser.BP_Laser")
cdo = unreal.get_default_object(laser.generated_class())
for prop in ("LaserActive", "UseFlashlight", "UseIRLaser", "PrimaryActorTick"):
    try:
        lines.append(f"CDO {prop}={cdo.get_editor_property(prop)!r}")
    except Exception as exc:
        lines.append(f"CDO {prop} ERR {exc}")

OUT.write_text("\n".join(lines))
