"""Dump exact bone geometry of Anim_Arms_Pistol_Idle for IK target design."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_pistol_pose_geo.log")
lines = []

seq = unreal.load_asset("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Pistol/Anim_Arms_Pistol_Idle.Anim_Arms_Pistol_Idle")
opts = unreal.AnimPoseEvaluationOptions()
pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(seq, 0.0, opts)

BONES = [
    "root", "pelvis", "spine_03", "spine_05", "neck_01", "head",
    "clavicle_r", "upperarm_r", "lowerarm_r", "hand_r",
    "clavicle_l", "upperarm_l", "lowerarm_l", "hand_l",
]

for b in BONES:
    try:
        t = unreal.AnimPoseExtensions.get_bone_pose(pose, b, unreal.AnimPoseSpaces.WORLD)
        v = t.translation
        r = t.rotation.rotator()
        lines.append(f"{b}: loc=({v.x:.1f}, {v.y:.1f}, {v.z:.1f}) rot=(P{r.pitch:.1f} Y{r.yaw:.1f} R{r.roll:.1f})")
    except Exception as exc:
        lines.append(f"{b}: ERR {exc}")

# arm segment lengths
def dist(a, b):
    ta = unreal.AnimPoseExtensions.get_bone_pose(pose, a, unreal.AnimPoseSpaces.WORLD).translation
    tb = unreal.AnimPoseExtensions.get_bone_pose(pose, b, unreal.AnimPoseSpaces.WORLD).translation
    return ((ta.x - tb.x) ** 2 + (ta.y - tb.y) ** 2 + (ta.z - tb.z) ** 2) ** 0.5

lines.append(f"upperarm_r len={dist('upperarm_r','lowerarm_r'):.1f}")
lines.append(f"lowerarm_r len={dist('lowerarm_r','hand_r'):.1f}")
lines.append(f"upperarm_l len={dist('upperarm_l','lowerarm_l'):.1f}")
lines.append(f"lowerarm_l len={dist('lowerarm_l','hand_l'):.1f}")

OUT.write_text("\n".join(lines))
print("done")
