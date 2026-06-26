"""Dump all non-default properties on weapon blueprints."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_weapon_props.log")
lines = []

for path in (
    "/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_EmptyHands.BP_Weapon_EmptyHands",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Pistol/BP_Weapon_Pistol.BP_Weapon_Pistol",
):
    asset = unreal.load_asset(path)
    cdo = unreal.get_default_object(asset.generated_class())
    lines.append(f"=== {path.split('/')[-1]} ===")
    for name in sorted(dir(cdo)):
        if name.startswith("_"):
            continue
        try:
            val = cdo.get_editor_property(name)
        except Exception:
            continue
        if val is None or val == "" or val is False:
            continue
        if isinstance(val, (int, float)) and val == 0:
            continue
        if isinstance(val, float) and val == 1.0:
            continue
        if hasattr(val, "get_path_name"):
            lines.append(f"  {name}={val.get_path_name()}")
        elif isinstance(val, (int, float, str, bool)):
            lines.append(f"  {name}={val!r}")

OUT.write_text("\n".join(lines))
