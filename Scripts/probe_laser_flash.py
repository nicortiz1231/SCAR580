"""Probe ENUM_Laser values and SpawnAttachments laser branch."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_laser_flash.log")
lines = []

# enum values
enum_asset = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Enums/ENUM_Laser.ENUM_Laser")
if enum_asset:
    lines.append(f"ENUM_Laser={enum_asset}")
    try:
        for name in enum_asset.get_editor_property("names"):
            lines.append(f"  enum {name}")
    except Exception as exc:
        lines.append(f"  names ERR {exc}")

# probe automatic base SpawnAttachments laser switch
bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase")
for graph in unreal.BlueprintEditorLibrary.list_graphs(bp):
    gname = graph.get_name()
    if "SpawnAttachments" not in gname and gname != "EventGraph":
        continue
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    for node in ed.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if any(k in title.upper() for k in ("LASER", "FLASH", "LIGHT", "BEAM", "SPOT", "ENUM_LASER", "SM_LASER")):
            lines.append(f"{gname}: {node.get_name()} | {title}")

# item base components
item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
handles = []
try:
    from unreal import SubobjectDataSubsystem, SubobjectDataBlueprintFunctionLibrary
    sub = unreal.get_editor_subsystem(SubobjectDataSubsystem)
    handles = sub.k2_gather_subobject_data_for_blueprint(item)
except Exception as exc:
    lines.append(f"subobject ERR {exc}")

for handle in handles:
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
    if not obj:
        continue
    name = obj.get_name()
    cls = obj.get_class().get_name()
    if any(k in name.upper() for k in ("LASER", "LIGHT", "FLASH", "BEAM", "MUZZLE")):
        lines.append(f"COMP {name} | {cls}")

OUT.write_text("\n".join(lines))
