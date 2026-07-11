"""Ensure assault rifle AimDistanceFromCamera is 20 and save."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/apply_rifle_aim_distance.log")
RIFLE_PATH = "/Game/BodycamFPSKIT/Blueprints/Interactables/AmericanRifle/BP_Weapon_AmericanRifle"
AUTO_BASE_PATH = "/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase"
TARGET = 20.0


def log(msg: str) -> None:
    prev = LOG.read_text() if LOG.exists() else ""
    LOG.write_text(prev + msg + "\n")
    unreal.log(f"[rifle_aim_distance] {msg}")


def set_aim_distance(bp, path: str, label: str) -> None:
    cdo = unreal.get_default_object(bp.generated_class())
    old = float(cdo.get_editor_property("AimDistanceFromCamera"))
    if abs(old - TARGET) > 0.001:
        cdo.set_editor_property("AimDistanceFromCamera", TARGET)
        log(f"{label} AimDistanceFromCamera {old} -> {TARGET}")
    else:
        log(f"{label} AimDistanceFromCamera already {old}")
    bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    rifle_bp = unreal.load_asset(f"{RIFLE_PATH}.BP_Weapon_AmericanRifle")
    auto_bp = unreal.load_asset(f"{AUTO_BASE_PATH}.BP_Weapon_AutomaticBase")
    if not rifle_bp or not auto_bp:
        raise RuntimeError("Missing rifle assets")

    set_aim_distance(rifle_bp, RIFLE_PATH, "AmericanRifle")
    set_aim_distance(auto_bp, AUTO_BASE_PATH, "AutomaticBase")
    log("Saved")


main()
