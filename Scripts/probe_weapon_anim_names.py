"""List arms anims per weapon folder + SKM_Camera skeleton."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_weapon_anim_names.log")
lines = []

for a in unreal.EditorAssetLibrary.list_assets("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims", recursive=True):
    if "/Weapon/" in a:
        continue
    lines.append(a.split(".")[0])

cam = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Camera/SKM_Camera.SKM_Camera")
skel = cam.get_editor_property("skeleton") if cam else None
lines.append(f"SKM_Camera skeleton: {skel.get_path_name() if skel else None}")

OUT.write_text("\n".join(lines))
print("done")
