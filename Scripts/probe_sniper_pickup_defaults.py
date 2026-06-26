"""Compare sniper vs rifle pickup attachment and ADS defaults."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sniper_pickup_defaults.log")
lines = []


def log(msg: str) -> None:
    lines.append(msg)
    unreal.log(msg)


ATTACH_PROPS = (
    "Item Data AttachmentsSight",
    "Item Data AttachmentsLaser",
    "Item Data AttachmentsMuzzle",
    "Item Data Attachments Grip",
    "Item Data Ammo Count",
    "Item Data Max Ammo",
    "Item Data Weapon Data",
    "AimDistanceFromCamera",
    "ChangeSightSpeed",
    "ScopeMat_SightDistance",
    "ScopeMat_GradientParam",
    "OpticSightMesh",
    "ScopeSightMesh",
)


for path in (
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Pickup_Sniper.BP_Weapon_Pickup_Sniper",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/AmericanRifle/BP_Weapon_Pickup_AmericanRifle.BP_Weapon_Pickup_AmericanRifle",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper",
):
    asset = unreal.load_asset(path)
    if not asset:
        continue
    cdo = unreal.get_default_object(asset.generated_class())
    lines.append(f"=== {path.split('/')[-1]} ===")
    for prop in ATTACH_PROPS:
        try:
            val = cdo.get_editor_property(prop)
            lines.append(f"  {prop}={val!r}")
        except Exception as exc:
            lines.append(f"  {prop} ERR {exc}")

# Dump all properties on sniper weapon CDO containing aim/scope/sight/attach
sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
cdo = unreal.get_default_object(sniper.generated_class())
lines.append("=== BP_Weapon_Sniper all relevant props ===")
for name in sorted(dir(cdo)):
    if name.startswith("_"):
        continue
    lower = name.lower()
    if not any(k in lower for k in ("aim", "scope", "sight", "attach", "fov", "distance", "item")):
        continue
    try:
        val = cdo.get_editor_property(name)
        if val is not None and val != "" and val is not False:
            if hasattr(val, "get_path_name"):
                lines.append(f"  {name}={val.get_path_name()}")
            else:
                lines.append(f"  {name}={val!r}")
    except Exception:
        pass

# ENUM_Sights members from pickup sight value type
pickup = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Pickup_Sniper.BP_Weapon_Pickup_Sniper"
)
pickup_cdo = unreal.get_default_object(pickup.generated_class())
sight = pickup_cdo.get_editor_property("Item Data AttachmentsSight")
lines.append(f"sniper_pickup_sight_type={type(sight)}")
enum_cls = type(sight)
for name in sorted(dir(enum_cls)):
    if name.isupper() or name.startswith("NEW"):
        try:
            lines.append(f"  ENUM_Sights.{name}={getattr(enum_cls, name)!r}")
        except Exception:
            pass

OUT.write_text("\n".join(lines))
