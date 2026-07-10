"""Ensure sniper BasePoseLoc matches editor tweak and save assets."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/apply_sniper_base_pose.log")
SNIPER_PATH = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper"
DT_PATH = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/DT_SniperAnimationValues"

TARGET = unreal.Vector(-15.860442, 27.665443, 8.180836)


def log(msg: str) -> None:
    prev = LOG.read_text() if LOG.exists() else ""
    LOG.write_text(prev + msg + "\n")
    unreal.log(f"[sniper_base_pose] {msg}")


def fmt(v: unreal.Vector) -> str:
    return f"({v.x:.6f},{v.y:.6f},{v.z:.6f})"


def set_base_pose_loc(owner, label: str) -> None:
    wv = owner.get_editor_property("WeaponValues")
    old = wv.get_editor_property("BasePoseLoc")
    log(f"{label} before {fmt(old)}")
    wv.set_editor_property("BasePoseLoc", TARGET)
    owner.set_editor_property("WeaponValues", wv)
    new = owner.get_editor_property("WeaponValues").get_editor_property("BasePoseLoc")
    log(f"{label} after  {fmt(new)}")


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    sniper_bp = unreal.load_asset(f"{SNIPER_PATH}.BP_Weapon_Sniper")
    dt = unreal.load_asset(f"{DT_PATH}.DT_SniperAnimationValues")
    if not sniper_bp or not dt:
        raise RuntimeError("Missing sniper BP or DT asset")

    set_base_pose_loc(dt, "DT")

    cdo = unreal.get_default_object(sniper_bp.generated_class())
    pv = cdo.get_editor_property("ProceduralValues")
    if pv:
        old = pv.get_editor_property("WeaponValues").get_editor_property("BasePoseLoc")
        log(f"BP ProceduralValues before {fmt(old)}")
        wv = pv.get_editor_property("WeaponValues")
        wv.set_editor_property("BasePoseLoc", TARGET)
        pv.set_editor_property("WeaponValues", wv)
        cdo.set_editor_property("ProceduralValues", pv)
        new = cdo.get_editor_property("ProceduralValues").get_editor_property("WeaponValues").get_editor_property("BasePoseLoc")
        log(f"BP ProceduralValues after  {fmt(new)}")

    dt.modify()
    sniper_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(sniper_bp)
    unreal.EditorAssetLibrary.save_asset(DT_PATH, only_if_is_dirty=False)
    unreal.EditorAssetLibrary.save_asset(SNIPER_PATH, only_if_is_dirty=False)
    log("Saved DT + BP_Weapon_Sniper")


main()
