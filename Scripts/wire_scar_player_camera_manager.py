"""Wire ASCARPlayerCameraManager onto the FPS player controller used by GM_SCAR_AR."""
import unreal
from pathlib import Path

GM_FP = "/Game/BodycamFPSKIT/Blueprints/GameModes/GM_FP.GM_FP"
CAMERA_MANAGER_CLASS = "/Script/SCAR.SCARPlayerCameraManager"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/wire_scar_player_camera_manager.log")


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[wire_pcm] {msg}")


def set_prop(obj, names, value) -> bool:
    for name in names:
        try:
            obj.set_editor_property(name, value)
            log(f"Set {obj.get_name()}.{name} = {value.get_name() if value else value}")
            return True
        except Exception as exc:
            log(f"Skip {name}: {exc}")
    return False


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    gm_fp = unreal.load_asset(GM_FP)
    if not gm_fp:
        raise RuntimeError(f"Missing {GM_FP}")

    gm_cdo = unreal.get_default_object(gm_fp.generated_class())
    pc_class = gm_cdo.get_editor_property("player_controller_class")
    if not pc_class:
        raise RuntimeError("GM_FP has no player_controller_class")

    pcm_class = unreal.load_class(None, CAMERA_MANAGER_CLASS)
    if not pcm_class:
        raise RuntimeError("SCARPlayerCameraManager not compiled — build SCAR module first")

    pc_cdo = unreal.get_default_object(pc_class)
    current = pc_cdo.get_editor_property("player_camera_manager_class")
    if current and current.get_name() == pcm_class.get_name():
        log("PlayerCameraManagerClass already set on PlayerController CDO")
        return

    if not set_prop(pc_cdo, ("player_camera_manager_class", "PlayerCameraManagerClass"), pcm_class):
        raise RuntimeError("Failed to set PlayerCameraManagerClass on PlayerController CDO")

    log(f"PlayerController class: {pc_class.get_path_name()}")
    log("Done")


main()
