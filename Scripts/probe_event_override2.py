import unreal
from pathlib import Path
OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_event_override2.log")
lines = []
sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
node = unreal.BlueprintEditorLibrary.add_event_override(sniper, "SpawnAttachments", unreal.IntPoint(400, 400))
lines.append(f"node={node} title={node.get_node_title() if node else None}")
if node:
    then = node.find_output_pin("then")
    lines.append(f"then links={len(list(unreal.BlueprintGraphPinLibrary.list_connected_pins(then))) if then else 0}")
unreal.BlueprintEditorLibrary.compile_blueprint(sniper)
unreal.EditorAssetLibrary.save_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper", only_if_is_dirty=False)
OUT.write_text("\n".join(lines))
