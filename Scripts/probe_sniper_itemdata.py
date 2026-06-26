"""Read BP_Weapon_Sniper ItemData default and add scope via BeginPlay if needed."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sniper_itemdata.log")
lines = []

sniper_bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
cdo = unreal.get_default_object(sniper_bp.generated_class())

for prop in dir(cdo):
    if prop.startswith("_"):
        continue
    lower = prop.lower()
    if "item" in lower or "data" in lower or "attach" in lower or "sight" in lower or "scope" in lower or "aim" in lower:
        try:
            val = cdo.get_editor_property(prop)
            if val is not None and val != "" and val is not False:
                lines.append(f"{prop}={val!r}")
        except Exception:
            pass

# Compare rifle weapon defaults
rifle = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/AmericanRifle/BP_Weapon_AmericanRifle.BP_Weapon_AmericanRifle"
)
rcdo = unreal.get_default_object(rifle.generated_class())
lines.append("=== rifle compare ===")
for prop in ("ItemData", "AimDistanceFromCamera", "OpticSightMesh", "ScopeSightMesh"):
    try:
        lines.append(f"rifle {prop}={rcdo.get_editor_property(prop)!r}")
        lines.append(f"sniper {prop}={cdo.get_editor_property(prop)!r}")
    except Exception as exc:
        lines.append(f"{prop} ERR {exc}")

OUT.write_text("\n".join(lines))
