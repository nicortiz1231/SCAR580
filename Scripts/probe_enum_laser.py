"""Read ENUM_Laser byte values."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_enum_laser.log")
lines = []

enum_obj = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Enums/ENUM_Laser.ENUM_Laser")
lines.append(f"enum={enum_obj}")
if enum_obj:
    for name in unreal.EnumLibrary.get_enum_names(enum_obj):
        val = unreal.EnumLibrary.get_enum_value_by_name(enum_obj, name)
        display = unreal.EnumLibrary.get_display_name(enum_obj, name)
        lines.append(f"  {name} = {val} display={display}")

OUT.write_text("\n".join(lines))
unreal.log(f"[probe_enum_laser] wrote {OUT}")
