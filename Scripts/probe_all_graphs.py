import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_all_graphs.log")
lines = []

for bp_path in (
    "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper",
):
    bp = unreal.load_asset(bp_path)
    lines.append(f"=== {bp_path.split('/')[-1]} ===")
    for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
        lines.append(f"  {g.get_name()}")

OUT.write_text("\n".join(lines))
