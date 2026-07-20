"""Bake TP-readable reload sequences for remote mannequins.

For each kit FP reload clip:
  Out[t] = Idle[0] * Inverse(Reload[0]) * Reload[t]   (local space, arm/IK bones)
  Other bones stay frozen at Idle[0] so the standing hold framing remains.

Writes /Game/SCAR580/Animations/TPReload/Anim_TP_* without modifying kit assets.
"""
from __future__ import annotations

import math
from pathlib import Path

import unreal

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/bake_tp_reload_anims.log")
DST_DIR = "/Game/SCAR580/Animations/TPReload"

JOBS = [
    (
        "Anim_TP_Pistol_Reload",
        "/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Pistol/Anim_Arms_Pistol_Reload.Anim_Arms_Pistol_Reload",
        "/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Pistol/Anim_Arms_Pistol_Idle.Anim_Arms_Pistol_Idle",
    ),
    (
        "Anim_TP_Pistol_ReloadEmpty",
        "/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Pistol/Anim_Arms_Pistol_ReloadEmpty.Anim_Arms_Pistol_ReloadEmpty",
        "/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Pistol/Anim_Arms_Pistol_Idle.Anim_Arms_Pistol_Idle",
    ),
    (
        "Anim_TP_AmericanRifle_Reload",
        "/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Rifle/Anim_Arms_AmericanRifle_Reload.Anim_Arms_AmericanRifle_Reload",
        "/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Rifle/Anim_Arms_AmericanRifle_Pose.Anim_Arms_AmericanRifle_Pose",
    ),
    (
        "Anim_TP_AmericanRifle_ReloadEmpty",
        "/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Rifle/Anim_Arms_AmericanRifle_ReloadEmpty.Anim_Arms_AmericanRifle_ReloadEmpty",
        "/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Rifle/Anim_Arms_AmericanRifle_Pose.Anim_Arms_AmericanRifle_Pose",
    ),
    (
        "Anim_TP_Shotgun_ReloadBegin",
        "/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Shotgun/Anim_Arms_Shotgun_ReloadBegin.Anim_Arms_Shotgun_ReloadBegin",
        "/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Shotgun/Anim_Arms_Shotgun_Idle.Anim_Arms_Shotgun_Idle",
    ),
    (
        "Anim_TP_Shotgun_ReloadEmptyBegin",
        "/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Shotgun/Anim_Arms_Shotgun_ReloadEmptyBegin.Anim_Arms_Shotgun_ReloadEmptyBegin",
        "/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Shotgun/Anim_Arms_Shotgun_Idle.Anim_Arms_Shotgun_Idle",
    ),
    (
        "Anim_TP_Sniper_Reload",
        "/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Sniper/Anim_Arms_Sniper_Reload.Anim_Arms_Sniper_Reload",
        "/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Sniper/Anim_Arms_Sniper__Idle.Anim_Arms_Sniper__Idle",
    ),
    (
        "Anim_TP_Sniper_ReloadEmpty",
        "/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Sniper/Anim_Arms_Sniper_Reload_Empty.Anim_Arms_Sniper_Reload_Empty",
        "/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Sniper/Anim_Arms_Sniper__Idle.Anim_Arms_Sniper__Idle",
    ),
]

ARM_BONE_PREFIXES = (
    "clavicle_",
    "upperarm_",
    "lowerarm_",
    "hand_",
    "thumb_",
    "index_",
    "middle_",
    "ring_",
    "pinky_",
    "weapon_",
    "ik_hand",
    "ik_gun",
)

lines: list[str] = []


def log(msg: str) -> None:
    lines.append(str(msg))
    unreal.log(f"[bake_tp_reload] {msg}")


def q_from_unreal(q):
    return (q.x, q.y, q.z, q.w)


def q_to_unreal(q):
    return unreal.Quat(q[0], q[1], q[2], q[3])


def q_mul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
        aw * bw - ax * bx - ay * by - az * bz,
    )


def q_inv(q):
    x, y, z, w = q
    n = x * x + y * y + z * z + w * w
    return (-x / n, -y / n, -z / n, w / n)


def q_norm(q):
    x, y, z, w = q
    n = math.sqrt(x * x + y * y + z * z + w * w)
    if n < 1e-12:
        return (0.0, 0.0, 0.0, 1.0)
    return (x / n, y / n, z / n, w / n)


def is_arm_bone(name: str) -> bool:
    lower = name.lower()
    return any(lower.startswith(p) or lower == p.rstrip("_") for p in ARM_BONE_PREFIXES)


def sample_local(seq, time_sec: float, bone: str):
    opts = unreal.AnimPoseEvaluationOptions()
    pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(seq, time_sec, opts)
    t = unreal.AnimPoseExtensions.get_bone_pose(pose, bone, unreal.AnimPoseSpaces.LOCAL)
    scl = getattr(t, "scale3d", None)
    if scl is None:
        scale = (1.0, 1.0, 1.0)
    else:
        scale = (scl.x, scl.y, scl.z)
    return (
        (t.translation.x, t.translation.y, t.translation.z),
        q_from_unreal(t.rotation),
        scale,
    )


def bake_one(dst_name: str, reload_path: str, idle_path: str) -> bool:
    reload_seq = unreal.load_asset(reload_path)
    idle_seq = unreal.load_asset(idle_path)
    if not reload_seq or not idle_seq:
        log(f"SKIP {dst_name}: missing reload={bool(reload_seq)} idle={bool(idle_seq)}")
        return False

    dst = f"{DST_DIR}/{dst_name}"
    if not unreal.EditorAssetLibrary.does_directory_exist(DST_DIR):
        unreal.EditorAssetLibrary.make_directory(DST_DIR)

    if unreal.EditorAssetLibrary.does_asset_exist(dst):
        try:
            unreal.EditorAssetLibrary.delete_asset(dst)
        except Exception as exc:
            log(f"  delete_asset soft-fail: {exc}")

    dup = unreal.EditorAssetLibrary.duplicate_asset(reload_path.split(".")[0], dst)
    if not dup:
        log(f"FAILED duplicate {dst_name}")
        return False

    new_seq = unreal.load_asset(dst)
    if not new_seq:
        log(f"FAILED load {dst}")
        return False

    controller = new_seq.get_editor_property("controller")
    model = controller.get_model_interface()
    num_keys = model.get_number_of_keys()
    play_len = float(new_seq.get_play_length())
    if num_keys < 2 or play_len <= 0.0:
        log(f"SKIP {dst_name}: keys={num_keys} len={play_len}")
        return False

    track_names = [str(n) for n in model.get_bone_track_names()]
    bones = list(track_names)
    log(f"  {dst_name}: tracks={len(bones)} keys={num_keys}")

    idle0 = {}
    ref0 = {}
    for bone in bones:
        try:
            idle0[bone] = sample_local(idle_seq, 0.0, bone)
            ref0[bone] = sample_local(reload_seq, 0.0, bone)
        except Exception as exc:
            log(f"  warn sample0 {bone}: {exc}")

    if not idle0:
        log(f"FAILED {dst_name}: no bones sampled")
        return False

    times = [play_len * (i / float(num_keys - 1)) for i in range(num_keys)]
    pos_by_bone = {b: [] for b in idle0}
    rot_by_bone = {b: [] for b in idle0}
    scl_by_bone = {b: [] for b in idle0}

    for t in times:
        for bone, (idle_t, idle_q, idle_s) in idle0.items():
            ref_t, ref_q, _ = ref0[bone]
            try:
                rel_t, rel_q, _ = sample_local(reload_seq, t, bone)
            except Exception:
                rel_t, rel_q = ref_t, ref_q

            if is_arm_bone(bone):
                out_q = q_norm(q_mul(idle_q, q_mul(q_inv(ref_q), rel_q)))
                out_t = (
                    idle_t[0] + (rel_t[0] - ref_t[0]),
                    idle_t[1] + (rel_t[1] - ref_t[1]),
                    idle_t[2] + (rel_t[2] - ref_t[2]),
                )
                out_s = idle_s
            else:
                out_q = idle_q
                out_t = idle_t
                out_s = idle_s

            pos_by_bone[bone].append(unreal.Vector(*out_t))
            rot_by_bone[bone].append(q_to_unreal(out_q))
            scl_by_bone[bone].append(unreal.Vector(*out_s))

    controller.open_bracket(f"SCAR bake TP reload {dst_name}")
    wrote = 0
    try:
        for bone in pos_by_bone:
            if len(pos_by_bone[bone]) != num_keys:
                continue
            try:
                controller.set_bone_track_keys(
                    bone,
                    pos_by_bone[bone],
                    rot_by_bone[bone],
                    scl_by_bone[bone],
                )
                wrote += 1
            except Exception as exc:
                log(f"  set_bone_track_keys {bone} failed: {exc}")
        log(f"OK {dst_name}: keys={num_keys} len={play_len:.2f}s tracks_written={wrote}")
    finally:
        controller.close_bracket()

    unreal.EditorAssetLibrary.save_asset(dst)
    return wrote > 0


def main() -> None:
    if OUT.exists():
        OUT.unlink()

    ok = 0
    for dst_name, reload_path, idle_path in JOBS:
        if bake_one(dst_name, reload_path, idle_path):
            ok += 1

    log(f"done: {ok}/{len(JOBS)} baked")
    OUT.write_text("\n".join(lines))


main()
