"""Trace BP_Weapon_Pickup_Sniper and BP_Item_Pickup equip flow."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_pickup_equip_flow.log")
lines = []

pickup = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Pickup_Sniper.BP_Weapon_Pickup_Sniper")
cdo = unreal.get_default_object(pickup.generated_class())
lines.append("=== Pickup sniper CDO ItemData ===")
try:
    idata = cdo.get_editor_property("ItemData")
    lines.append(f"  WeaponData={idata.get_editor_property('WeaponData').get_path_name() if idata else None}")
    att = idata.get_editor_property("Attachments")
    lines.append(f"  Attachments Sight={att.get_editor_property('Sight')}")
    lines.append(f"  Attachments Laser={att.get_editor_property('Laser')}")
    lines.append(f"  Attachments Muzzle={att.get_editor_property('Muzzle')}")
    lines.append(f"  AmmoCount={idata.get_editor_property('AmmoCount')} MaxAmmo={idata.get_editor_property('MaxAmmo')}")
except Exception as exc:
    lines.append(f"  ERR {exc}")

# generic pickup parent
base_pickup = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Pickup.BP_Item_Pickup")
if base_pickup:
    ped = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(base_pickup))
    lines.append("\n=== BP_Item_Pickup overlap/equip chain ===")
    for node in ped.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if any(k in title for k in ("Overlap", "Equip", "SetWeaponAmmoData", "SpawnActor", "SpawnedItem")):
            lines.append(f"  {node.get_name()} | {title}")
    # trace from SetWeaponAmmoData
    for node in ped.list_all_nodes():
        if "SetWeaponAmmoData" not in str(node.get_node_title()):
            continue
        lines.append(f"\n=== {node.get_name()} SetWeaponAmmoData wiring ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            linked = [f"{lp.get_owning_node().get_name()}:{unreal.BlueprintGraphPinLibrary.get_pin_name(lp)}" for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            if linked or val:
                lines.append(f"  {pn} -> {linked or val}")

OUT.write_text("\n".join(lines))
