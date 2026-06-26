import unreal
from pathlib import Path
OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_camera_clip.log")
lines = []
bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
for handle in sds.k2_gather_subobject_data_for_blueprint(bp):
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(
        unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    )
    if not obj or "FirstPersonCamera" not in obj.get_name():
        continue
    lines.append(f"=== {obj.get_name()} ===")
    for prop in sorted(dir(obj)):
        if prop.startswith("_"):
            continue
        lower = prop.lower()
        if "clip" in lower or "near" in lower:
            try:
                lines.append(f"  {prop}={obj.get_editor_property(prop)!r}")
            except Exception as exc:
                lines.append(f"  {prop} ERR {exc}")

# sniper procedural values asset props
dt = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/DT_SniperAnimationValues.DT_SniperAnimationValues")
lines.append(f"=== DT class {dt.get_class().get_name()} ===")
for prop in sorted(dir(dt)):
    if prop.startswith("_"):
        continue
    try:
        val = dt.get_editor_property(prop)
        if val is not None and val != "" and val is not False:
            lines.append(f"  {prop}={val!r}")
    except Exception:
        pass

# sniper CDO ProceduralValues if any
sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
cdo = unreal.get_default_object(sniper.generated_class())
for prop in ("ProceduralValues",):
    try:
        lines.append(f"sniper.{prop}={cdo.get_editor_property(prop)!r}")
    except Exception as exc:
        lines.append(f"sniper.{prop} ERR {exc}")

OUT.write_text("\n".join(lines))
