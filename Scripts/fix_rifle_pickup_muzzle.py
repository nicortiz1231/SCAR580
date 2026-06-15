"""Remove default suppressor from the American Rifle secondary weapon pickup."""

import unreal
from pathlib import Path

PICKUP = "/Game/BodycamFPSKIT/Blueprints/Interactables/AmericanRifle/BP_Weapon_Pickup_AmericanRifle"
LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR/Scripts/fix_rifle_pickup_muzzle.log")


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[fix_rifle_pickup_muzzle] {msg}")


def no_suppressor_value(current):
    enum_type = type(current)
    for name in dir(enum_type):
        if name.startswith("_"):
            continue
        candidate = getattr(enum_type, name)
        if not isinstance(candidate, enum_type):
            continue
        if "SUPRESSOR" in str(name).upper() or "SUPPRESSOR" in str(name).upper():
            continue
        if int(candidate.value) == 0:
            return candidate
    raise RuntimeError(f"Could not find no-suppressor enum entry on {enum_type}")


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    bp = unreal.load_asset(PICKUP)
    if not bp:
        raise RuntimeError(f"Failed to load {PICKUP}")

    cdo = unreal.get_default_object(bp.generated_class())
    prop = "Item Data AttachmentsMuzzle"
    current = cdo.get_editor_property(prop)
    target = no_suppressor_value(current)
    log(f"{prop}: {current!r} -> {target!r}")

    if current == target:
        log("Already set to no suppressor")
        return

    cdo.set_editor_property(prop, target)
    bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(PICKUP, only_if_is_dirty=False)
    log("Saved BP_Weapon_Pickup_AmericanRifle without default suppressor")


main()
