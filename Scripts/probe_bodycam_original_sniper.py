"""Read original Bodycam sniper + pickup defaults from BODYCAMFPSKIT project."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_bodycam_original_sniper.log")
lines = []

paths = (
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Pickup_Sniper.BP_Weapon_Pickup_Sniper",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/DT_SniperAnimationValues.DT_SniperAnimationValues",
)

for path in paths:
    asset = unreal.load_asset(path)
    if not asset:
        lines.append(f"MISSING {path}")
        continue
    lines.append(f"=== {path.split('/')[-1]} ===")
    if "DT_" in path:
        for row in unreal.DataTableFunctionLibrary.get_data_table_row_names(asset):
            ok, row_data = unreal.DataTableFunctionLibrary.get_data_table_row_from_name(asset, row)
            if not ok:
                continue
            wv = row_data.get_editor_property("WeaponValues")
            loc = wv.get_editor_property("BasePoseLoc")
            rot = wv.get_editor_property("BasePoseRot")
            lines.append(f"  BasePoseLoc=({loc.x},{loc.y},{loc.z})")
            lines.append(f"  BasePoseRot=({rot.roll},{rot.pitch},{rot.yaw})")
        continue

    cdo = unreal.get_default_object(asset.generated_class())
    for prop in (
        "AimDistanceFromCamera", "ChangeSightSpeed", "ScopeMat_SightDistance", "ScopeMat_GradientParam",
        "ScopeSightMesh", "OpticSightMesh", "ProceduralValues",
        "Item Data AttachmentsSight", "Item Data AttachmentsLaser",
        "Item Data AttachmentsMuzzle", "Item Data Attachments Grip",
        "Item Data Ammo Count", "Item Data Max Ammo",
    ):
        try:
            val = cdo.get_editor_property(prop)
            if hasattr(val, "get_path_name"):
                val = val.get_path_name()
            lines.append(f"  {prop}={val!r}")
        except Exception as exc:
            lines.append(f"  {prop} ERR {exc}")

# sniper graph summary from original
sniper = unreal.load_asset(paths[0])
for gname in ("EventGraph", "UserConstructionScript"):
    g = next((g for g in unreal.BlueprintEditorLibrary.list_graphs(sniper) if g.get_name() == gname), None)
    if not g:
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append(f"=== ORIGINAL sniper {gname} ===")
    for node in editor.list_all_nodes():
        lines.append(f"  {node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')}")

item = unreal.load_asset(paths[2])
ied = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(item))
for node in ied.list_all_nodes():
    if node.get_class().get_name() != "K2Node_CustomEvent":
        continue
    if "SpawnAttachments" not in str(node.get_node_title()):
        continue
    lines.append("=== ORIGINAL item SpawnAttachments ===")
    then = node.find_output_pin("then")
    linked = []
    if then:
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
            linked.append(lp.get_owning_node().get_name())
    lines.append(f"  then -> {linked or 'NONE'}")

OUT.write_text("\n".join(lines))
