"""Final sniper ADS clip fix — slightly stronger forward pull from current tuned values."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_sniper_forward_nudge.log")
DT_PATH = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/DT_SniperAnimationValues"
SNIPER_PATH = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper"

# Target values: ~20% Y / ~16% Z below Bodycam original, enough to clear near clip entirely.
TARGET_BASE_POSE_LOC = unreal.Vector(-10.93, 26.10, 9.25)
AIM_DISTANCE = 9.0


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[sniper_forward] {msg}")


def tweak_dt_pose(dt) -> None:
    wv = dt.get_editor_property("WeaponValues")
    loc = wv.get_editor_property("BasePoseLoc")
    x, y, z = float(loc.x), float(loc.y), float(loc.z)
    wv.set_editor_property("BasePoseLoc", TARGET_BASE_POSE_LOC)
    dt.set_editor_property("WeaponValues", wv)
    dt.modify()
    unreal.EditorAssetLibrary.save_asset(DT_PATH, only_if_is_dirty=False)
    t = TARGET_BASE_POSE_LOC
    log(f"BasePoseLoc ({x:.2f},{y:.2f},{z:.2f}) -> ({t.x:.2f},{t.y:.2f},{t.z:.2f})")


def tweak_aim_distance(sniper_bp) -> None:
    cdo = unreal.get_default_object(sniper_bp.generated_class())
    current = float(cdo.get_editor_property("AimDistanceFromCamera"))
    cdo.set_editor_property("AimDistanceFromCamera", AIM_DISTANCE)
    sniper_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(sniper_bp)
    unreal.EditorAssetLibrary.save_asset(SNIPER_PATH, only_if_is_dirty=False)
    log(f"AimDistanceFromCamera {current} -> {AIM_DISTANCE}")


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    dt = unreal.load_asset(f"{DT_PATH}.DT_SniperAnimationValues")
    sniper = unreal.load_asset(f"{SNIPER_PATH}.BP_Weapon_Sniper")
    if not dt or not sniper:
        raise RuntimeError("Missing sniper DT or blueprint")

    tweak_dt_pose(dt)
    tweak_aim_distance(sniper)
    log("Done")


main()
