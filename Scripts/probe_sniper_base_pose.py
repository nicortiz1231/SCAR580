"""Read sniper BasePoseLoc from DT and BP CDO."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sniper_base_pose.log")
lines = []

dt = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/DT_SniperAnimationValues.DT_SniperAnimationValues"
)
sniper = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper"
)

if dt:
    row = unreal.DataTableFunctionLibrary.get_data_table_row_names(dt)
    for name in row:
        row_data = unreal.DataTableFunctionLibrary.get_data_table_row_from_name(dt, name)
        if row_data:
            wv = row_data.get_editor_property("WeaponValues")
            loc = wv.get_editor_property("BasePoseLoc")
            lines.append(f"DT[{name}] BasePoseLoc=({loc.x:.6f},{loc.y:.6f},{loc.z:.6f})")

if sniper:
    cdo = unreal.get_default_object(sniper.generated_class())
    pv = cdo.get_editor_property("ProceduralValues")
    if pv:
        wv = pv.get_editor_property("WeaponValues")
        loc = wv.get_editor_property("BasePoseLoc")
        lines.append(f"BP ProceduralValues BasePoseLoc=({loc.x:.6f},{loc.y:.6f},{loc.z:.6f})")
    try:
        wv2 = cdo.get_editor_property("WeaponValues")
        loc2 = wv2.get_editor_property("BasePoseLoc")
        lines.append(f"BP WeaponValues BasePoseLoc=({loc2.x:.6f},{loc2.y:.6f},{loc2.z:.6f})")
    except Exception:
        pass

OUT.write_text("\n".join(lines) + "\n")
for line in lines:
    unreal.log(line)
