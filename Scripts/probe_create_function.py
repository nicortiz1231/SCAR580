import unreal
from pathlib import Path
OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_create_function.log")
lines = []
sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
fn = getattr(unreal.BlueprintGraphEditor, "create_and_edit_function_graph", None)
lines.append(f"create_and_edit_function_graph={fn}")
for name in sorted(dir(unreal.BlueprintEditorLibrary)):
    if "function" in name.lower() or "event" in name.lower() or "override" in name.lower():
        lines.append(f"BEL.{name}")
OUT.write_text("\n".join(lines))
