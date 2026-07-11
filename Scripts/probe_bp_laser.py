"""Probe BP_Laser and laser toggle flow on item base."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_bp_laser.log")
lines = []

# BP_Laser
laser_bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Attachments/Laser/Blueprints/BP_Laser.BP_Laser")
lines.append(f"BP_Laser={laser_bp}")
if laser_bp:
    cls = laser_bp.generated_class()
    cdo = unreal.get_default_object(cls)
    for name in sorted(dir(cdo)):
        if any(k in name.upper() for k in ("LIGHT", "LASER", "FLASH", "DECAL", "BEAM", "MESH")):
            try:
                lines.append(f"  cdo.{name}={cdo.get_editor_property(name)!r}")
            except Exception:
                pass

# ToggleLaser / ToggleFlashlight on item base
item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for graph in unreal.BlueprintEditorLibrary.list_graphs(item):
    gname = graph.get_name()
    if gname not in ("ToggleLaser", "ToggleFlashlight", "SpawnAttachments", "EventGraph"):
        continue
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    lines.append(f"\n=== graph {gname} ===")
    for node in ed.list_all_nodes()[:40]:
        lines.append(f"  {node.get_name()} | {node.get_node_title()}")

# modding UI laser selection changed
wbp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Widgets/UI_WeaponModding.UI_WeaponModding")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(wbp))
for node in eg.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    if "Laser" in title and ("Selection" in title or "Spawn" in title or "Toggle" in title):
        lines.append(f"UI: {node.get_name()} | {title}")
        then = node.find_output_pin("then")
        if then:
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
                lines.append(f"  -> {lp.get_owning_node().get_node_title()}")

OUT.write_text("\n".join(lines))
