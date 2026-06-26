import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_enums.log")
lines = []

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
cdo = unreal.get_default_object(item.generated_class())

for prop in ("Item Data",):
    pass

# get sight from spawned sniper default item data via SetAmmo graph or switch enum
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    if g.get_name() != "SpawnAttachments":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if "Switch" in node.get_class().get_name() or "Scope" in title or "Sight" in title:
            lines.append(f"{node.get_name()} | {title}")

# enumerate user-defined enums used in project
for path in (
    "/Game/BodycamFPSKIT/Blueprints/Enums/ENUM_Sights",
    "/Game/BodycamFPSKIT/Blueprints/Enums/ENUM_Laser",
    "/Game/BodycamFPSKIT/Blueprints/Enums/ENUM_Muzzle",
):
    asset = unreal.load_asset(path)
    if not asset:
        lines.append(f"MISSING {path}")
        continue
    lines.append(f"=== {path} ===")
    try:
        for i, name in enumerate(asset.get_editor_property("display_name_map")):
            pass
    except Exception:
        pass
    try:
        entries = asset.get_editor_property("names")
        for i, n in enumerate(entries):
            lines.append(f"  [{i}] {n}")
    except Exception as exc:
        lines.append(f"  names ERR {exc}")

# sniper CDO aim
sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
cdo2 = unreal.get_default_object(sniper.generated_class())
lines.append(f"AimDistanceFromCamera={cdo2.get_editor_property('AimDistanceFromCamera')}")

OUT.write_text("\n".join(lines))
