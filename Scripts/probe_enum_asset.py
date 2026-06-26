import unreal
from pathlib import Path

lines = []
enum_asset = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Enums/ENUM_Sights.ENUM_Sights")
lines.append(f"enum={enum_asset}")
for prop in ("display_name_map", "names", "enum_values"):
    try:
        lines.append(f"{prop}={enum_asset.get_editor_property(prop)}")
    except Exception as exc:
        lines.append(f"{prop} ERR {exc}")

# UserDefinedEnum might expose entries differently
try:
    lines.append(f"num_enumerators={enum_asset.get_editor_property('NumEnums')}")
except Exception as exc:
    lines.append(f"NumEnums ERR {exc}")

Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_enum_asset.log").write_text("\n".join(lines))
