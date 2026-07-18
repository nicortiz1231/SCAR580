"""Create Anim_Arms_Pistol_ADS: pistol idle with arms extended via two-bone IK."""
import math
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/make_pistol_ads_anim.log")
lines = []


def log(msg):
    lines.append(str(msg))


# ---------- pure-python quaternion helpers (x, y, z, w) ----------
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
    return (x / n, y / n, z / n, w / n)


def q_rot(q, v):
    # rotate vector v by quaternion q
    qv = (v[0], v[1], v[2], 0.0)
    r = q_mul(q_mul(q, qv), q_inv(q))
    return (r[0], r[1], r[2])


def v_sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def v_add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def v_scale(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def v_dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def v_cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def v_len(a):
    return math.sqrt(v_dot(a, a))


def v_normed(a):
    l = v_len(a)
    return (a[0] / l, a[1] / l, a[2] / l)


def q_between(a, b):
    """Minimal rotation taking direction a to direction b."""
    an, bn = v_normed(a), v_normed(b)
    d = max(-1.0, min(1.0, v_dot(an, bn)))
    if d > 0.999999:
        return (0.0, 0.0, 0.0, 1.0)
    axis = v_cross(an, bn)
    if v_len(axis) < 1e-8:
        # opposite: pick any perpendicular axis
        axis = v_cross(an, (0.0, 0.0, 1.0))
        if v_len(axis) < 1e-8:
            axis = v_cross(an, (1.0, 0.0, 0.0))
    axis = v_normed(axis)
    ang = math.acos(d)
    s = math.sin(ang / 2.0)
    return q_norm((axis[0] * s, axis[1] * s, axis[2] * s, math.cos(ang / 2.0)))


# ---------- load source pose ----------
SRC = "/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Pistol/Anim_Arms_Pistol_Idle.Anim_Arms_Pistol_Idle"
DST_DIR = "/Game/SCAR580/Animations"
DST = f"{DST_DIR}/Anim_Arms_Pistol_ADS"

seq = unreal.load_asset(SRC)
opts = unreal.AnimPoseEvaluationOptions()
pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(seq, 0.0, opts)

ALL_BONES = [
    "clavicle_r", "upperarm_r", "lowerarm_r", "hand_r",
    "clavicle_l", "upperarm_l", "lowerarm_l", "hand_l",
    "ik_hand_root", "ik_hand_gun", "ik_hand_r", "ik_hand_l",
]

world = {}
local = {}
for b in ALL_BONES:
    tw = unreal.AnimPoseExtensions.get_bone_pose(pose, b, unreal.AnimPoseSpaces.WORLD)
    tl = unreal.AnimPoseExtensions.get_bone_pose(pose, b, unreal.AnimPoseSpaces.LOCAL)
    world[b] = ((tw.translation.x, tw.translation.y, tw.translation.z), q_from_unreal(tw.rotation))
    local[b] = ((tl.translation.x, tl.translation.y, tl.translation.z), q_from_unreal(tl.rotation))

log("=== source world transforms ===")
for b in ALL_BONES:
    p, q = world[b]
    log(f"  {b}: loc=({p[0]:.1f},{p[1]:.1f},{p[2]:.1f})")

# ---------- IK solve per arm ----------
def solve_arm(side, hand_target, pole):
    """Return dict bone->new local quat, plus new world transforms for hand/elbow."""
    upper = f"upperarm_{side}"
    lower = f"lowerarm_{side}"
    hand = f"hand_{side}"
    clav = f"clavicle_{side}"

    S = world[upper][0]
    E_old = world[lower][0]
    H_old = world[hand][0]

    L1 = v_len(v_sub(E_old, S))
    L2 = v_len(v_sub(H_old, E_old))

    T = hand_target
    d = v_len(v_sub(T, S))
    d = min(d, (L1 + L2) * 0.999)

    n = v_normed(v_sub(T, S))
    a = (L1 * L1 - L2 * L2 + d * d) / (2.0 * d)
    h = math.sqrt(max(0.0, L1 * L1 - a * a))
    p_perp = v_sub(pole, v_scale(n, v_dot(pole, n)))
    p_perp = v_normed(p_perp)
    E_new = v_add(v_add(S, v_scale(n, a)), v_scale(p_perp, h))

    # world rotations via minimal delta from old bone directions
    q_upper_old = world[upper][1]
    q_lower_old = world[lower][1]
    q_hand_old = world[hand][1]
    q_clav = world[clav][1]

    q_upper_new = q_norm(q_mul(q_between(v_sub(E_old, S), v_sub(E_new, S)), q_upper_old))
    q_lower_new = q_norm(q_mul(q_between(v_sub(H_old, E_old), v_sub(T, E_new)), q_lower_old))
    q_hand_new = q_hand_old  # keep grip/aim orientation

    # locals: parent chain clavicle -> upper -> lower -> hand
    lq_upper = q_norm(q_mul(q_inv(q_clav), q_upper_new))
    lq_lower = q_norm(q_mul(q_inv(q_upper_new), q_lower_new))
    lq_hand = q_norm(q_mul(q_inv(q_lower_new), q_hand_new))

    return {
        upper: lq_upper,
        lower: lq_lower,
        hand: lq_hand,
    }, (E_new, T, q_hand_new)


# targets (component space: +Y forward, +Z up; right hand is -X side)
HR_OLD = world["hand_r"][0]
HL_OLD = world["hand_l"][0]
HAND_OFFSET = v_sub(HL_OLD, HR_OLD)  # preserve two-hand grip relationship

HR_TARGET = (-4.0, 40.0, 150.0)
HL_TARGET = v_add(HR_TARGET, HAND_OFFSET)

new_locals, (er, hr, qhr) = solve_arm("r", HR_TARGET, (-1.0, 0.0, -0.6))
locals_l, (el, hl, qhl) = solve_arm("l", HL_TARGET, (1.0, 0.0, -0.6))
new_locals.update(locals_l)

log(f"solved elbow_r=({er[0]:.1f},{er[1]:.1f},{er[2]:.1f}) hand_r target=({hr[0]:.1f},{hr[1]:.1f},{hr[2]:.1f})")
log(f"solved elbow_l=({el[0]:.1f},{el[1]:.1f},{el[2]:.1f}) hand_l target=({hl[0]:.1f},{hl[1]:.1f},{hl[2]:.1f})")

# ---------- ik bones follow the hands (weapon attaches to ik_hand_gun) ----------
# Convention check: how does ik_hand_gun relate to hand_r in the source?
ik_gun_w = world["ik_hand_gun"]
rel_gun_to_handr_t = q_rot(q_inv(world["hand_r"][1]), v_sub(ik_gun_w[0], world["hand_r"][0]))
rel_gun_to_handr_q = q_norm(q_mul(q_inv(world["hand_r"][1]), ik_gun_w[1]))
log(f"ik_hand_gun offset from hand_r: t=({rel_gun_to_handr_t[0]:.2f},{rel_gun_to_handr_t[1]:.2f},{rel_gun_to_handr_t[2]:.2f})")

# New ik_hand_gun world = new hand_r world composed with the same relative offset
ik_gun_new_q = q_norm(q_mul(qhr, rel_gun_to_handr_q))
ik_gun_new_t = v_add(HR_TARGET, q_rot(qhr, rel_gun_to_handr_t))

# ik_hand_root: keep source local (usually identity at root)
ik_root_w = world["ik_hand_root"]

# ik_hand_gun local (parent = ik_hand_root, unchanged)
ik_gun_lq = q_norm(q_mul(q_inv(ik_root_w[1]), ik_gun_new_q))
ik_gun_lt = q_rot(q_inv(ik_root_w[1]), v_sub(ik_gun_new_t, ik_root_w[0]))

# ik_hand_r / ik_hand_l: world should match hand_r / hand_l; parent = ik_hand_gun (new)
def ik_child_local(hand_t, hand_q):
    lq = q_norm(q_mul(q_inv(ik_gun_new_q), hand_q))
    lt = q_rot(q_inv(ik_gun_new_q), v_sub(hand_t, ik_gun_new_t))
    return lt, lq

# preserve the source relationship between ik_hand_r/l and hand_r/l
def src_rel(ik_bone, hand_bone):
    t = q_rot(q_inv(world[hand_bone][1]), v_sub(world[ik_bone][0], world[hand_bone][0]))
    q = q_norm(q_mul(q_inv(world[hand_bone][1]), world[ik_bone][1]))
    return t, q

rel_r_t, rel_r_q = src_rel("ik_hand_r", "hand_r")
rel_l_t, rel_l_q = src_rel("ik_hand_l", "hand_l")

ik_r_world_q = q_norm(q_mul(qhr, rel_r_q))
ik_r_world_t = v_add(HR_TARGET, q_rot(qhr, rel_r_t))
ik_l_world_q = q_norm(q_mul(qhl, rel_l_q))
ik_l_world_t = v_add(HL_TARGET, q_rot(qhl, rel_l_t))

ik_r_lt, ik_r_lq = ik_child_local(ik_r_world_t, ik_r_world_q)
ik_l_lt, ik_l_lq = ik_child_local(ik_l_world_t, ik_l_world_q)

# ---------- duplicate asset and write tracks ----------
if unreal.EditorAssetLibrary.does_asset_exist(DST):
    unreal.EditorAssetLibrary.delete_asset(DST)

dup = unreal.EditorAssetLibrary.duplicate_asset(SRC.split(".")[0], DST)
if not dup:
    log("FAILED to duplicate asset")
    OUT.write_text("\n".join(lines))
    raise SystemExit(1)

new_seq = unreal.load_asset(DST)
controller = new_seq.get_editor_property("controller")
model = controller.get_model_interface()
num_keys = model.get_number_of_keys()
log(f"duplicated -> {DST}, keys={num_keys}")


existing_tracks = [str(n) for n in model.get_bone_track_names()]
log(f"existing tracks: {len(existing_tracks)}")


def write_track(bone, l_trans, l_quat):
    if bone not in existing_tracks:
        controller.add_bone_curve(bone)
        existing_tracks.append(bone)
    pos_keys = [unreal.Vector(*l_trans)] * num_keys
    rot_keys = [q_to_unreal(l_quat)] * num_keys
    scale_keys = [unreal.Vector(1.0, 1.0, 1.0)] * num_keys
    controller.set_bone_track_keys(bone, pos_keys, rot_keys, scale_keys)


controller.open_bracket("SCAR ADS pose edit")
try:
    for bone in ("upperarm_r", "lowerarm_r", "hand_r", "upperarm_l", "lowerarm_l", "hand_l"):
        lt = local[bone][0]  # keep source local translation (bone length)
        write_track(bone, lt, new_locals[bone])
    write_track("ik_hand_gun", ik_gun_lt, ik_gun_lq)
    write_track("ik_hand_r", ik_r_lt, ik_r_lq)
    write_track("ik_hand_l", ik_l_lt, ik_l_lq)
finally:
    controller.close_bracket()

unreal.EditorAssetLibrary.save_asset(DST)
log("saved")

# ---------- verify ----------
new_seq2 = unreal.load_asset(DST)
pose2 = unreal.AnimPoseExtensions.get_anim_pose_at_time(new_seq2, 0.0, opts)
log("=== verification (new asset, world space) ===")
for b in ("upperarm_r", "lowerarm_r", "hand_r", "hand_l", "ik_hand_gun", "ik_hand_r", "ik_hand_l", "head"):
    t = unreal.AnimPoseExtensions.get_bone_pose(pose2, b, unreal.AnimPoseSpaces.WORLD)
    v = t.translation
    r = t.rotation.rotator()
    log(f"  {b}: loc=({v.x:.1f},{v.y:.1f},{v.z:.1f}) rot=(P{r.pitch:.1f} Y{r.yaw:.1f} R{r.roll:.1f})")

OUT.write_text("\n".join(lines))
print("done")
