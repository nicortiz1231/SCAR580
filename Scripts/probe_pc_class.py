import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_pc_class.log")
lines = []

def p(msg):
    lines.append(str(msg))
    unreal.log(str(msg))

gm = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/GameModes/GM_FP.GM_FP")
cdo = unreal.get_default_object(gm.generated_class())
pc = cdo.get_editor_property("player_controller_class")
p(f"PC class={pc}")
p(f"PC name={pc.get_name()}")
p(f"PC path={pc.get_path_name()}")

try:
    pcm = cdo.get_editor_property("player_camera_manager_class")
    p(f"PCM on GM? {pcm}")
except Exception as e:
    p(f"GM pcm err {e}")

pc_cdo = unreal.get_default_object(pc)
try:
    pcm = pc_cdo.get_editor_property("player_camera_manager_class")
    p(f"PCM on PC CDO={pcm}")
except Exception as e:
    p(f"PC pcm err {e}")

OUT.write_text("\n".join(lines))
