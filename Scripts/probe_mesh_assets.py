"""Compare sniper mesh assets SCAR vs original Bodycam."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_mesh_assets.log")
lines = []

paths = [
    "/Game/BodycamFPSKIT/Demo/Meshes/SM_4xScopeForSniper",
    "/Game/BodycamFPSKIT/Demo/Meshes/SM_SightSniper",
    "/Game/BodycamFPSKIT/Demo/Meshes/SM_Sniper",
]

for p in paths:
    a = unreal.load_asset(p)
    lines.append(f"{p} -> {'OK' if a else 'MISSING'}")

sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
cdo = unreal.get_default_object(sniper.generated_class())
mesh = cdo.get_editor_property("Mesh")
lines.append(f"sniper.Mesh={mesh.get_name() if mesh else None}")
item_mesh = cdo.get_editor_property("Item_Mesh")
sk = item_mesh.get_editor_property("skeletal_mesh") if item_mesh else None
lines.append(f"sniper Item_Mesh SK={sk.get_name() if sk else None}")

OUT.write_text("\n".join(lines))
