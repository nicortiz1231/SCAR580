"""Remove LeftMouseButton -> IA_Shoot so iOS touch does not fire everywhere."""
import unreal
from pathlib import Path

IMC_PLAYER = "/Game/BodycamFPSKIT/Input/IMC_Player"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_imc_remove_lmb_shoot.log")


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[imc_lmb] {msg}")


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()
    imc = unreal.load_asset(f"{IMC_PLAYER}.IMC_Player")
    if not imc:
        raise RuntimeError(f"Missing {IMC_PLAYER}")

    dkm = imc.get_editor_property("default_key_mappings")
    mappings = list(dkm.get_editor_property("mappings"))
    kept = []
    removed = 0
    for mapping in mappings:
        action = mapping.get_editor_property("action")
        key = mapping.get_editor_property("key")
        key_name = str(key.get_editor_property("key_name")) if key else ""
        if action and action.get_name() == "IA_Shoot" and key_name == "LeftMouseButton":
            removed += 1
            log(f"Removed mapping IA_Shoot <- LeftMouseButton")
            continue
        kept.append(mapping)

    if removed:
        dkm.set_editor_property("mappings", kept)
        imc.set_editor_property("default_key_mappings", dkm)
        unreal.EditorAssetLibrary.save_asset(IMC_PLAYER, only_if_is_dirty=False)
        log(f"Saved IMC_Player ({removed} mapping(s) removed)")
    else:
        log("LeftMouseButton -> IA_Shoot already absent")


main()
