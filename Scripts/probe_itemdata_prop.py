"""Find ItemData property on weapon class."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_itemdata_prop.log")
lines = []

sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
cls = sniper.generated_class()
cdo = unreal.get_default_object(cls)
lines.append(f"class={cls.get_name()}")
for name in sorted(dir(cdo)):
    if "item" in name.lower() or "data" in name.lower():
        lines.append(f"  {name}")
        try:
            lines.append(f"    ={cdo.get_editor_property(name)!r}")
        except Exception as exc:
            lines.append(f"    ERR {exc}")

# parent class
parent = cls.get_super_class()
lines.append(f"parent={parent.get_name()}")
pcdo = unreal.get_default_object(parent)
for name in sorted(dir(pcdo)):
    if "item" in name.lower():
        try:
            val = pcdo.get_editor_property(name)
            lines.append(f"  parent.{name}={val!r}")
        except Exception:
            pass

OUT.write_text("\n".join(lines))
