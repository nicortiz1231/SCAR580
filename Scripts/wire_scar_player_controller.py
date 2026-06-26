"""Point GM_FP / GM_SCAR_AR at ASCARPlayerController so camera manager persists in cooked builds."""
import unreal
from pathlib import Path

PC_CLASS = "/Script/SCAR.SCARPlayerController"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/wire_scar_player_controller.log")

GAME_MODES = (
    "/Game/BodycamFPSKIT/Blueprints/GameModes/GM_FP.GM_FP",
    "/Game/SCAR580/Blueprints/GameModes/GM_SCAR_AR.GM_SCAR_AR",
)


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[wire_pc] {msg}")


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    pc_class = unreal.load_class(None, PC_CLASS)
    if not pc_class:
        raise RuntimeError("ASCARPlayerController not compiled")

    for gm_path in GAME_MODES:
        gm = unreal.load_asset(gm_path)
        if not gm:
            log(f"Skip missing {gm_path}")
            continue
        cdo = unreal.get_default_object(gm.generated_class())
        current = cdo.get_editor_property("player_controller_class")
        if current and current.get_name() == pc_class.get_name():
            log(f"{gm_path}: already SCARPlayerController")
            continue
        cdo.set_editor_property("player_controller_class", pc_class)
        log(f"{gm_path}: {current.get_name() if current else None} -> SCARPlayerController")
        gm.modify()
        unreal.BlueprintEditorLibrary.compile_blueprint(gm)
        unreal.EditorAssetLibrary.save_asset(gm_path.split(".")[0], only_if_is_dirty=False)

    log("Done")


main()
