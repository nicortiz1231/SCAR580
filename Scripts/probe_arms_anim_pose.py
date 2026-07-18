"""Evaluate arms-hold anims on SKM_Manny: hand/leg bone poses vs ref pose."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_arms_anim_pose.log")
lines = []


def log(msg):
    lines.append(str(msg))


mesh = unreal.load_asset("/Game/BodycamFPSKIT/Demo/Character/Mannequins/Meshes/SKM_Manny.SKM_Manny")
BONES = ["hand_r", "hand_l", "ik_hand_gun", "thigh_r", "calf_r", "foot_r", "pelvis", "head", "spine_03"]

ANIMS = [
    "/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Pistol/Anim_Arms_Pistol_Idle.Anim_Arms_Pistol_Idle",
    "/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Rifle/Anim_Arms_AmericanRifle_Pose.Anim_Arms_AmericanRifle_Pose",
]

# Reference pose
ref_pose = unreal.AnimPose.get_ref_pose(mesh)
ref = {}
for b in BONES:
    try:
        t = ref_pose.get_bone_pose(b, unreal.AnimPoseSpaces.WORLD)
        ref[b] = t.translation
    except Exception as exc:
        log(f"ref {b} err: {exc}")

log("=== ref pose (component space) ===")
for b, v in ref.items():
    log(f"  {b}: ({v.x:.1f}, {v.y:.1f}, {v.z:.1f})")

for anim_path in ANIMS:
    anim = unreal.load_asset(anim_path)
    if not anim:
        log(f"=== {anim_path} MISSING ===")
        continue
    log(f"=== {anim.get_name()} @t=0 ===")
    try:
        pose = unreal.AnimPose.get_anim_pose_at_time(anim, 0.0)
        for b in BONES:
            try:
                t = pose.get_bone_pose(b, unreal.AnimPoseSpaces.WORLD)
                v = t.translation
                r = ref.get(b)
                delta = ((v.x - r.x) ** 2 + (v.y - r.y) ** 2 + (v.z - r.z) ** 2) ** 0.5 if r else -1
                log(f"  {b}: ({v.x:.1f}, {v.y:.1f}, {v.z:.1f}) dRef={delta:.1f}")
            except Exception as exc:
                log(f"  {b} err: {exc}")
    except Exception as exc:
        log(f"  pose eval err: {exc}")

OUT.write_text("\n".join(lines))
print("done")
