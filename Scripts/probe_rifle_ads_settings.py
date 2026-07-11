"""Read assault rifle ADS-related settings at current project state."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_rifle_ads_settings.log")
lines = []

RIFLE = "/Game/BodycamFPSKIT/Blueprints/Interactables/AmericanRifle/BP_Weapon_AmericanRifle"
DT = "/Game/BodycamFPSKIT/Blueprints/Interactables/AmericanRifle/DT_RifleAnimationValues"

rifle_bp = unreal.load_asset(f"{RIFLE}.BP_Weapon_AmericanRifle")
dt = unreal.load_asset(f"{DT}.DT_RifleAnimationValues")
cdo = unreal.get_default_object(rifle_bp.generated_class())

lines.append(f"AimDistanceFromCamera={cdo.get_editor_property('AimDistanceFromCamera')}")

for block_name in ("WeaponValues",):
    block = dt.get_editor_property(block_name)
    wv = block if block_name == "WeaponValues" else block
    if block_name == "WeaponValues":
        wv = dt.get_editor_property("WeaponValues")
    for prop in (
        "BasePoseLoc", "BasePoseRot", "AimPoseLoc", "AimPoseRot",
        "SprintPoseLoc", "CrouchPoseLoc",
    ):
        try:
            val = wv.get_editor_property(prop)
            if hasattr(val, "x"):
                lines.append(f"DT.{prop}=({val.x:.4f},{val.y:.4f},{val.z:.4f})")
            else:
                lines.append(f"DT.{prop}={val!r}")
        except Exception as exc:
            lines.append(f"DT.{prop} ERR {exc}")

pv = cdo.get_editor_property("ProceduralValues")
if pv:
    wv2 = pv.get_editor_property("WeaponValues")
    loc = wv2.get_editor_property("BasePoseLoc")
    lines.append(f"BP ProceduralValues.BasePoseLoc=({loc.x:.4f},{loc.y:.4f},{loc.z:.4f})")

OUT.write_text("\n".join(lines))
