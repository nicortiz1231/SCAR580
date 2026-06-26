import unreal
from pathlib import Path
OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_camera_dt_simple.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
for handle in sds.k2_gather_subobject_data_for_blueprint(bp):
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(
        unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    )
    if not obj or "FirstPersonCamera" not in obj.get_name():
        continue
    lines.append(f"camera={obj.get_name()}")
    for prop in sorted(dir(obj)):
        if "clip" in prop.lower() or "near" in prop.lower():
            try:
                lines.append(f"  {prop}={obj.get_editor_property(prop)!r}")
            except Exception as exc:
                lines.append(f"  {prop} ERR {exc}")

# sniper DT rows via export path string
for path in (
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/DT_SniperAnimationValues",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Pistol/DT_PistolAnimationValues",
):
    dt = unreal.load_asset(path)
    lines.append(f"DT {path.split('/')[-1]} = {dt}")
    if not dt:
        continue
    try:
        rows = unreal.DataTableFunctionLibrary.get_data_table_row_names(dt)
        lines.append(f"  rows={list(rows)}")
        for row in rows:
            ok, out = unreal.DataTableFunctionLibrary.get_data_table_row_from_name(dt, row)
            lines.append(f"  row {row} ok={ok} type={type(out).__name__ if ok else None}")
            if ok:
                for prop in sorted(dir(out)):
                    if prop.startswith("_"):
                        continue
                    if "recoil" in prop.lower() or "weapon" in prop.lower() or "aim" in prop.lower():
                        try:
                            val = out.get_editor_property(prop)
                            lines.append(f"    {prop}={val!r}")
                        except Exception:
                            pass
    except Exception as exc:
        lines.append(f"  rows ERR {exc}")

OUT.write_text("\n".join(lines))
