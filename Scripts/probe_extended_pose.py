"""Rank all SK_Mannequin anims by right-hand forward extension (aim pose search)."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_extended_pose.log")
lines = []

mesh = unreal.load_asset("/Game/BodycamFPSKIT/Demo/Character/Mannequins/Meshes/SKM_Manny.SKM_Manny")

registry = unreal.AssetRegistryHelpers.get_asset_registry()
filt = unreal.ARFilter(
    class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "AnimSequence")],
    recursive_paths=True,
    package_paths=["/Game"],
)
assets = registry.get_assets(filt)

results = []
for ad in assets:
    seq = ad.get_asset()
    if not seq:
        continue
    skel = seq.get_editor_property("skeleton")
    if not skel or skel.get_name() != "SK_Mannequin":
        continue
    try:
        opts = unreal.AnimPoseEvaluationOptions()
        pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(seq, 0.0, opts)
        hand = unreal.AnimPoseExtensions.get_bone_pose(pose, "hand_r", unreal.AnimPoseSpaces.WORLD).translation
        head = unreal.AnimPoseExtensions.get_bone_pose(pose, "head", unreal.AnimPoseSpaces.WORLD).translation
        pelvis = unreal.AnimPoseExtensions.get_bone_pose(pose, "pelvis", unreal.AnimPoseSpaces.WORLD).translation
        hand_l = unreal.AnimPoseExtensions.get_bone_pose(pose, "hand_l", unreal.AnimPoseSpaces.WORLD).translation
        fwd = hand.x - pelvis.x  # component-space forward extension
        height = hand.z
        head_dist = ((hand.x - head.x) ** 2 + (hand.y - head.y) ** 2 + (hand.z - head.z) ** 2) ** 0.5
        hands_apart = ((hand.x - hand_l.x) ** 2 + (hand.y - hand_l.y) ** 2 + (hand.z - hand_l.z) ** 2) ** 0.5
        results.append((fwd, head_dist, height, hands_apart, str(ad.package_name)))
    except Exception as exc:
        lines.append(f"ERR {ad.asset_name}: {exc}")

results.sort(reverse=True)
lines.append("fwd(X) | distToHead | handZ | handsApart | asset")
for fwd, head_dist, height, apart, name in results:
    lines.append(f"{fwd:7.1f} | {head_dist:6.1f} | {height:6.1f} | {apart:6.1f} | {name}")

OUT.write_text("\n".join(lines))
print("done")
