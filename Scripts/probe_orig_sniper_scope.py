"""Read original Bodycam sniper scope params."""
import unreal
from pathlib import Path
OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_orig_sniper_scope.log")
lines = []
sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
cdo = unreal.get_default_object(sniper.generated_class())
for prop in ("AimDistanceFromCamera", "ScopeMat_SightDistance", "ScopeMat_GradientParam", "ChangeSightSpeed"):
    lines.append(f"{prop}={cdo.get_editor_property(prop)!r}")
scope = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Attachments/Scope/Blueprints/BP_Scope.BP_Scope")
scdo = unreal.get_default_object(scope.generated_class())
for prop in sorted(dir(scdo)):
    if prop.startswith("_"):
        continue
    if "radius" in prop.lower() or "render" in prop.lower():
        try:
            lines.append(f"BP_Scope.{prop}={scdo.get_editor_property(prop)!r}")
        except Exception:
            pass
OUT.write_text("\n".join(lines))
