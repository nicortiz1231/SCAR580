import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_anim_api.log")
lines = []

seq = unreal.load_asset("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Pistol/Anim_Arms_Pistol_Idle.Anim_Arms_Pistol_Idle")
ctrl = seq.get_editor_property("controller")
lines.append(f"controller: {ctrl}")
if ctrl:
    lines.append("CTRL METHODS: " + ", ".join(m for m in dir(ctrl) if not m.startswith("_")))

model = seq.get_editor_property("data_model")
lines.append(f"data_model: {model}")

# AnimPose bone names?
opts = unreal.AnimPoseEvaluationOptions()
pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(seq, 0.0, opts)
lines.append("POSE EXT: " + ", ".join(m for m in dir(unreal.AnimPoseExtensions) if not m.startswith("_")))
try:
    names = unreal.AnimPoseExtensions.get_bone_names(pose)
    lines.append(f"bone count: {len(names)}; first 10: {[str(n) for n in names[:10]]}")
except Exception as e:
    lines.append(f"get_bone_names err {e}")

OUT.write_text("\n".join(lines))
