import unreal
from pathlib import Path
OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_recoil_dir.log")
lines = []
sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
pv = unreal.get_default_object(sniper.generated_class()).get_editor_property("ProceduralValues")
rv = pv.get_editor_property("RecoilValues")
lines.append(f"RecoilValues={rv}")
for prop in sorted(dir(rv)):
    if prop.startswith("_"):
        continue
    try:
        v = rv.get_editor_property(prop)
        lines.append(f"  {prop}={v!r}")
    except Exception as exc:
        lines.append(f"  {prop} ERR {exc}")
OUT.write_text("\n".join(lines))
