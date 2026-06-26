"""Find ScopeRenderRadius and related scope props on weapon blueprints."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_scope_render_radius.log")
lines = []

paths = [
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Item_Base",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/AmericanRifle/BP_Weapon_AmericanRifle",
]

scope_props = (
    "ScopeRenderRadius",
    "ScopeMat_SightDistance",
    "ScopeMat_GradientParam",
    "AimDistanceFromCamera",
    "ChangeSightSpeed",
)

for path in paths:
    name = path.rsplit("/", 1)[-1]
    bp = unreal.load_asset(f"{path}.{name}")
    if not bp:
        lines.append(f"\n=== {name} MISSING ===")
        continue
    cdo = unreal.get_default_object(bp.generated_class())
    lines.append(f"\n=== {name} ===")
    for prop in scope_props:
        try:
            lines.append(f"  {prop}={cdo.get_editor_property(prop)!r}")
        except Exception as e:
            lines.append(f"  {prop}=ERR:{e}")

    # scan all properties containing scope/render/radius
    for prop in sorted(dir(cdo)):
        if prop.startswith("_"):
            continue
        lower = prop.lower()
        if any(k in lower for k in ("scope", "render", "radius", "sight", "gradient", "aim")):
            if prop in scope_props:
                continue
            try:
                v = cdo.get_editor_property(prop)
                if isinstance(v, (int, float, bool, str)) or (hasattr(v, "x") and not hasattr(v, "pitch")):
                    lines.append(f"  {prop}={v!r}")
            except Exception:
                pass

OUT.write_text("\n".join(lines))
