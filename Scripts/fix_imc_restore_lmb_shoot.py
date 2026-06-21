"""Restore LeftMouseButton -> IA_Shoot for TouchInterface shoot button."""
import unreal
from pathlib import Path

IMC_PLAYER = "/Game/BodycamFPSKIT/Input/IMC_Player"
IA_SHOOT = "/Game/BodycamFPSKIT/Input/Actions/IA_Shoot"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_imc_restore_lmb_shoot.log")


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[imc_restore_lmb] {msg}")


def has_lmb_mapping(mappings) -> bool:
    for mapping in mappings:
        action = mapping.get_editor_property("action")
        key = mapping.get_editor_property("key")
        if not action or not key:
            continue
        if action.get_name() == "IA_Shoot" and str(key.get_editor_property("key_name")) == "LeftMouseButton":
            return True
    return False


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()
    imc = unreal.load_asset(f"{IMC_PLAYER}.IMC_Player")
    shoot = unreal.load_asset(f"{IA_SHOOT}.IA_Shoot")
    if not imc or not shoot:
        raise RuntimeError("Missing IMC_Player or IA_Shoot")

    dkm = imc.get_editor_property("default_key_mappings")
    mappings = list(dkm.get_editor_property("mappings"))
    if has_lmb_mapping(mappings):
        log("LeftMouseButton -> IA_Shoot already present")
        return

    entry = unreal.EnhancedActionKeyMapping()
    entry.set_editor_property("action", shoot)
    key = unreal.Key()
    key.set_editor_property("key_name", unreal.Name("LeftMouseButton"))
    entry.set_editor_property("key", key)
    mappings.append(entry)
    dkm.set_editor_property("mappings", mappings)
    imc.set_editor_property("default_key_mappings", dkm)
    unreal.EditorAssetLibrary.save_asset(IMC_PLAYER, only_if_is_dirty=False)
    log("Restored LeftMouseButton -> IA_Shoot (TouchInterface shoot button only)")


main()
