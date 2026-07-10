"""Ensure assault rifle BasePoseLoc/Rot match editor tweaks and save assets."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/apply_rifle_base_pose.log")
RIFLE_PATH = "/Game/BodycamFPSKIT/Blueprints/Interactables/AmericanRifle/BP_Weapon_AmericanRifle"
DT_PATH = "/Game/BodycamFPSKIT/Blueprints/Interactables/AmericanRifle/DT_RifleAnimationValues"

TARGET_LOC = unreal.Vector(-8.088402, 29.213047, 4.905493)
# Bodycam UI X/Y/Z maps to roll/pitch/yaw on BasePoseRot.
TARGET_ROT = unreal.Rotator(-25.0, -91.571495, 25.492521)


def log(msg: str) -> None:
    prev = LOG.read_text() if LOG.exists() else ""
    LOG.write_text(prev + msg + "\n")
    unreal.log(f"[rifle_base_pose] {msg}")


def fmt_vec(v: unreal.Vector) -> str:
    return f"({v.x:.6f},{v.y:.6f},{v.z:.6f})"


def fmt_rot(r: unreal.Rotator) -> str:
    return f"(r{r.roll:.6f},p{r.pitch:.6f},y{r.yaw:.6f})"


def set_weapon_values(owner, label: str) -> None:
    wv = owner.get_editor_property("WeaponValues")
    old_loc = wv.get_editor_property("BasePoseLoc")
    old_rot = wv.get_editor_property("BasePoseRot")
    log(f"{label} BasePoseLoc before {fmt_vec(old_loc)}")
    log(f"{label} BasePoseRot before {fmt_rot(old_rot)}")
    wv.set_editor_property("BasePoseLoc", TARGET_LOC)
    wv.set_editor_property("BasePoseRot", TARGET_ROT)
    owner.set_editor_property("WeaponValues", wv)
    new_wv = owner.get_editor_property("WeaponValues")
    log(f"{label} BasePoseLoc after  {fmt_vec(new_wv.get_editor_property('BasePoseLoc'))}")
    log(f"{label} BasePoseRot after  {fmt_rot(new_wv.get_editor_property('BasePoseRot'))}")


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    rifle_bp = unreal.load_asset(f"{RIFLE_PATH}.BP_Weapon_AmericanRifle")
    dt = unreal.load_asset(f"{DT_PATH}.DT_RifleAnimationValues")
    if not rifle_bp or not dt:
        raise RuntimeError("Missing rifle BP or DT asset")

    set_weapon_values(dt, "DT")

    cdo = unreal.get_default_object(rifle_bp.generated_class())
    pv = cdo.get_editor_property("ProceduralValues")
    if pv:
        wv = pv.get_editor_property("WeaponValues")
        log(f"BP ProceduralValues BasePoseLoc before {fmt_vec(wv.get_editor_property('BasePoseLoc'))}")
        log(f"BP ProceduralValues BasePoseRot before {fmt_rot(wv.get_editor_property('BasePoseRot'))}")
        wv.set_editor_property("BasePoseLoc", TARGET_LOC)
        wv.set_editor_property("BasePoseRot", TARGET_ROT)
        pv.set_editor_property("WeaponValues", wv)
        cdo.set_editor_property("ProceduralValues", pv)
        new_wv = cdo.get_editor_property("ProceduralValues").get_editor_property("WeaponValues")
        log(f"BP ProceduralValues BasePoseLoc after  {fmt_vec(new_wv.get_editor_property('BasePoseLoc'))}")
        log(f"BP ProceduralValues BasePoseRot after  {fmt_rot(new_wv.get_editor_property('BasePoseRot'))}")

    dt.modify()
    rifle_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(rifle_bp)
    unreal.EditorAssetLibrary.save_asset(DT_PATH, only_if_is_dirty=False)
    unreal.EditorAssetLibrary.save_asset(RIFLE_PATH, only_if_is_dirty=False)
    log("Saved DT + BP_Weapon_AmericanRifle")


main()
