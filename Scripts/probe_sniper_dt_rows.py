"""Read DT_SniperAnimationValues row data."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sniper_dt_rows.log")
lines = []

dt = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/DT_SniperAnimationValues.DT_SniperAnimationValues")
lines.append(f"dt={dt} class={dt.get_class().get_name()}")

# try row struct access
row_names = unreal.DataTableFunctionLibrary.get_data_table_row_names(dt)
lines.append(f"rows={list(row_names)}")

for row in row_names:
    success, out_row = unreal.DataTableFunctionLibrary.get_data_table_row_from_name(dt, row)
    lines.append(f"=== row {row} success={success} ===")
    if not success:
        continue
    for prop in sorted(dir(out_row)):
        if prop.startswith("_"):
            continue
        lower = prop.lower()
        if not any(k in lower for k in ("recoil", "ads", "weapon", "kick", "loc", "rot", "offset", "value", "alpha", "speed")):
            continue
        try:
            val = out_row.get_editor_property(prop)
            lines.append(f"  {prop}={val!r}")
        except Exception:
            pass

# pistol for compare
for path in (
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Pistol/DT_PistolAnimationValues.DT_PistolAnimationValues",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/DT_SniperAnimationValues.DT_SniperAnimationValues",
):
    asset = unreal.load_asset(path)
    if not asset:
        continue
    lines.append(f"--- {path.split('/')[-1]} ---")
    for row in unreal.DataTableFunctionLibrary.get_data_table_row_names(asset):
        success, out_row = unreal.DataTableFunctionLibrary.get_data_table_row_from_name(asset, row)
        if not success:
            continue
        for prop in ("WeaponValues", "RecoilValues", "ADS_Speed", "ADS_Alpha"):
            try:
                val = out_row.get_editor_property(prop)
                lines.append(f"  {row}.{prop}={val!r}")
            except Exception:
                pass

OUT.write_text("\n".join(lines))
