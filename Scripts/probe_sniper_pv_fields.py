"""Dump sniper ProceduralValues struct fields."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sniper_pv_fields.log")
lines = []

sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
cdo = unreal.get_default_object(sniper.generated_class())
pv = cdo.get_editor_property("ProceduralValues")

lines.append(f"pv={pv} class={pv.get_class().get_name()}")

for prop in ("WeaponValues", "RecoilValues"):
    try:
        val = pv.get_editor_property(prop)
        lines.append(f"=== {prop} ===")
        for sub in sorted(dir(val)):
            if sub.startswith("_"):
                continue
            try:
                sv = val.get_editor_property(sub)
                lines.append(f"  {sub}={sv!r}")
            except Exception:
                pass
    except Exception as exc:
        lines.append(f"{prop} ERR {exc}")

OUT.write_text("\n".join(lines))
