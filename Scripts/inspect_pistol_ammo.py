"""Inspect pistol ammo defaults."""

import unreal
from pathlib import Path

PATHS = [
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Pistol/BP_Weapon_Pistol",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Pistol/BP_Weapon_Pickup_Pistol",
    "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter",
]
LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR/Scripts/inspect_pistol_ammo.log")


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(msg)


def dump(obj, label: str) -> None:
    log(f"=== {label} ===")
    for name in (
        "AmmoCount",
        "MaxAmmo",
        "WeaponCapacity",
        "Item Data Ammo Count",
        "Item Data Max Ammo",
        "PrimarySlot",
    ):
        try:
            val = obj.get_editor_property(name)
            log(f"{name} = {val!r}")
            if name == "PrimarySlot" and val is not None:
                log(f"  PrimarySlot.AmmoCount = {val.get_editor_property('AmmoCount')!r}")
                log(f"  PrimarySlot.MaxAmmo = {val.get_editor_property('MaxAmmo')!r}")
                log(f"  PrimarySlot.WeaponCapacity = {val.get_editor_property('WeaponCapacity')!r}")
        except Exception as exc:
            log(f"{name}: unavailable ({exc})")


def main() -> None:
    if LOG.exists():
        LOG.unlink()
    for path in PATHS:
        bp = unreal.load_asset(path)
        if not bp:
            log(f"Missing {path}")
            continue
        cdo = unreal.get_default_object(bp.generated_class())
        dump(cdo, path)


main()
