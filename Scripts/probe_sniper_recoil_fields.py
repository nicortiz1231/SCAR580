"""Read sniper recoil struct fields from data table."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sniper_recoil_fields.log")
lines = []

dt = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/DT_SniperAnimationValues.DT_SniperAnimationValues"
)
rows = unreal.DataTableFunctionLibrary.get_data_table_row_names(dt)
lines.append(f"rows={list(rows)}")

for row in rows:
    ok, out = unreal.DataTableFunctionLibrary.get_data_table_row_from_name(dt, row)
    lines.append(f"row={row} ok={ok}")
    if not ok:
        continue
    for prop in sorted(dir(out)):
        if prop.startswith("_"):
            continue
        try:
            val = out.get_editor_property(prop)
            lines.append(f"  {prop}={val!r}")
            if hasattr(val, "get_editor_property"):
                for sub in sorted(dir(val)):
                    if sub.startswith("_"):
                        continue
                    try:
                        sv = val.get_editor_property(sub)
                        lines.append(f"    {sub}={sv!r}")
                    except Exception:
                        pass
        except Exception:
            pass

# AC_ProceduralRecoil defaults
ac = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Components/AC_ProceduralRecoil.AC_ProceduralRecoil"
)
cdo = unreal.get_default_object(ac.generated_class())
lines.append("=== AC_ProceduralRecoil CDO ===")
for name in sorted(dir(cdo)):
    if name.startswith("_"):
        continue
    lower = name.lower()
    if not any(k in lower for k in ("recoil", "kick", "back", "loc", "rot", "clip", "wall")):
        continue
    try:
        lines.append(f"  {name}={cdo.get_editor_property(name)!r}")
    except Exception:
        pass

OUT.write_text("\n".join(lines))
