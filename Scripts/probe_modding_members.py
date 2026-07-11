"""List UI_WeaponModding blueprint member variables."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_modding_members.log")
lines = []

wbp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Widgets/UI_WeaponModding.UI_WeaponModding")
for name in unreal.BlueprintEditorLibrary.list_member_variable_names(wbp):
    vtype = unreal.BlueprintEditorLibrary.get_member_variable_type(wbp, name)
    lines.append(f"{name} -> {vtype}")

OUT.write_text("\n".join(lines))
