"""Wire InventorySystem_0_5 into SCAR multiplayer: inventory PC + HUD + game mode."""

from __future__ import annotations

from pathlib import Path

import unreal

LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/setup_inventory_system.log")

SOURCE_PC = "/Game/InventorySystem_0_5/Core/PC_InventoryGame"
TARGET_PC = "/Game/SCAR580/Blueprints/BP_SCAR_InventoryPlayerController"
GM_AR_MP = "/Game/SCAR580/Blueprints/GameModes/GM_SCAR_AR_Multiplayer"
INVENTORY_HUD = "/Game/InventorySystem_0_5/Core/HUD_InventoryGame"

SCAR_MP_PC_CLASS = "/Script/SCAR.SCARARMultiplayerPlayerController"
INVENTORY_HUD_CLASS = f"{INVENTORY_HUD}.HUD_InventoryGame_C"


def log(msg: str) -> None:
    existing = LOG_PATH.read_text(encoding="utf-8") if LOG_PATH.exists() else ""
    LOG_PATH.write_text(existing + msg + "\n", encoding="utf-8")
    unreal.log(f"[setup_inventory_system] {msg}")


def set_prop(obj, names, value) -> bool:
    for name in names:
        try:
            obj.set_editor_property(name, value)
            log(f"Set {obj.get_name()}.{name} = {value}")
            return True
        except Exception as exc:
            log(f"Skip {name}: {exc}")
    return False


def ensure_directory(path: str) -> None:
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)
        log(f"Created directory {path}")


def ensure_inventory_player_controller() -> unreal.Blueprint:
    ensure_directory("/Game/SCAR580/Blueprints")

    if not unreal.EditorAssetLibrary.does_asset_exist(SOURCE_PC):
        raise RuntimeError(f"Missing source player controller {SOURCE_PC}")

    if not unreal.EditorAssetLibrary.does_asset_exist(TARGET_PC):
        duplicated = unreal.EditorAssetLibrary.duplicate_asset(SOURCE_PC, TARGET_PC)
        if not duplicated:
            raise RuntimeError(f"Failed to duplicate {SOURCE_PC} -> {TARGET_PC}")
        log(f"Created {TARGET_PC}")

    inventory_pc = unreal.load_asset(f"{TARGET_PC}.BP_SCAR_InventoryPlayerController")
    if not inventory_pc:
        raise RuntimeError(f"Failed to load {TARGET_PC}")

    inventory_hud_class = unreal.load_class(None, INVENTORY_HUD_CLASS)
    if not inventory_hud_class:
        raise RuntimeError(f"Missing inventory HUD class {INVENTORY_HUD_CLASS}")

    # Set HUDClass before reparenting while the BP still mirrors PC_InventoryGame defaults.
    pre_reparent_cdo = unreal.get_default_object(inventory_pc.generated_class())
    if not set_prop(pre_reparent_cdo, ("hud_class", "HUDClass"), inventory_hud_class):
        log("Warning: could not set HUDClass before reparent; runtime C++ will spawn inventory HUD")

    scar_pc_class = unreal.load_class(None, SCAR_MP_PC_CLASS)
    if not scar_pc_class:
        raise RuntimeError(
            "Missing compiled SCARARMultiplayerPlayerController; build the SCAR C++ module first"
        )

    current_parent = unreal.BlueprintEditorLibrary.get_blueprint_parent_class(inventory_pc)
    if current_parent != scar_pc_class:
        unreal.BlueprintEditorLibrary.reparent_blueprint(inventory_pc, scar_pc_class)
        log(f"Reparented inventory player controller -> {SCAR_MP_PC_CLASS}")
    else:
        log("Inventory player controller already parented to SCARARMultiplayerPlayerController")

    post_reparent_cdo = unreal.get_default_object(inventory_pc.generated_class())
    if not set_prop(post_reparent_cdo, ("hud_class", "HUDClass"), inventory_hud_class):
        log("Warning: could not set HUDClass after reparent; runtime C++ will spawn inventory HUD")

    unreal.BlueprintEditorLibrary.compile_blueprint(inventory_pc)
    unreal.EditorAssetLibrary.save_asset(TARGET_PC, only_if_is_dirty=False)
    log("Configured BP_SCAR_InventoryPlayerController")
    return inventory_pc


def configure_game_mode(inventory_pc: unreal.Blueprint) -> None:
    if not unreal.EditorAssetLibrary.does_asset_exist(GM_AR_MP):
        raise RuntimeError(f"Missing game mode {GM_AR_MP}")

    gm_bp = unreal.load_asset(f"{GM_AR_MP}.GM_SCAR_AR_Multiplayer")
    if not gm_bp:
        raise RuntimeError(f"Failed to load {GM_AR_MP}")

    inventory_pc_class = inventory_pc.generated_class()
    cdo = unreal.get_default_object(gm_bp.generated_class())
    set_prop(cdo, ("player_controller_class", "PlayerControllerClass"), inventory_pc_class)

    unreal.BlueprintEditorLibrary.compile_blueprint(gm_bp)
    unreal.EditorAssetLibrary.save_asset(GM_AR_MP, only_if_is_dirty=False)
    log("Configured GM_SCAR_AR_Multiplayer to use inventory player controller")


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    log("Starting inventory system setup")
    inventory_pc = ensure_inventory_player_controller()
    configure_game_mode(inventory_pc)
    log("Inventory system setup complete")


if __name__ == "__main__":
    main()
