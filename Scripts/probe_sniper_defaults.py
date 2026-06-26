"""Dump sniper weapon and pickup default item data."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sniper_defaults.log")
lines = []

for path in (
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Pickup_Sniper.BP_Weapon_Pickup_Sniper",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Pistol/BP_Weapon_Pickup_Pistol.BP_Weapon_Pickup_Pistol",
):
    asset = unreal.load_asset(path)
    if not asset:
        lines.append(f"MISSING {path}")
        continue
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
        lower = name.lower()
        if any(k in lower for k in ("ammo", "item", "weapon", "attach", "mag")):
            if hasattr(val, "get_path_name"):
                lines.append(f"  {name}={val.get_path_name()}")
            else:
                lines.append(f"  {name}={val!r}")

OUT.write_text("\n".join(lines))
