"""Set pistol magazine size to 17 rounds."""

import unreal
from pathlib import Path

PISTOL = "/Game/BodycamFPSKIT/Blueprints/Interactables/Pistol/BP_Weapon_Pistol"
PICKUP = "/Game/BodycamFPSKIT/Blueprints/Interactables/Pistol/BP_Weapon_Pickup_Pistol"
MAGAZINE_SIZE = 17
LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR/Scripts/fix_pistol_magazine_size.log")


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[fix_pistol_magazine_size] {msg}")


def set_if_changed(obj, prop: str, value: int) -> bool:
    current = obj.get_editor_property(prop)
    if current == value:
        log(f"{obj.get_name()}.{prop} already {value}")
        return False
    log(f"{obj.get_name()}.{prop}: {current} -> {value}")
    obj.set_editor_property(prop, value)
    return True


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    changed = False

    pistol_bp = unreal.load_asset(PISTOL)
    if not pistol_bp:
        raise RuntimeError(f"Failed to load {PISTOL}")
    pistol_cdo = unreal.get_default_object(pistol_bp.generated_class())
    changed |= set_if_changed(pistol_cdo, "AmmoCount", MAGAZINE_SIZE)
    changed |= set_if_changed(pistol_cdo, "WeaponCapacity", MAGAZINE_SIZE)
    if changed:
        pistol_bp.modify()
        unreal.BlueprintEditorLibrary.compile_blueprint(pistol_bp)
        unreal.EditorAssetLibrary.save_asset(PISTOL, only_if_is_dirty=False)

    pickup_bp = unreal.load_asset(PICKUP)
    if not pickup_bp:
        raise RuntimeError(f"Failed to load {PICKUP}")
    pickup_cdo = unreal.get_default_object(pickup_bp.generated_class())
    pickup_changed = set_if_changed(pickup_cdo, "Item Data Ammo Count", MAGAZINE_SIZE)
    if pickup_changed:
        pickup_bp.modify()
        unreal.BlueprintEditorLibrary.compile_blueprint(pickup_bp)
        unreal.EditorAssetLibrary.save_asset(PICKUP, only_if_is_dirty=False)
        changed = True

    if changed:
        log("Saved pistol magazine size changes")
    else:
        log("No changes needed")


main()
