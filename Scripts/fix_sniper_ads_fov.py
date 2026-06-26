"""Increase sniper scope ADS zoom via FOV only (hip-fire weapon distance unchanged)."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_sniper_ads_fov.log")
CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
SELECT_NODE = "K2Node_Select_5"
SNIPER_FOV_ENUM = "NewEnumerator14"  # wired from ENUM_Sights NewEnumerator7 scope ADS
SNIPER_ADS_FOV = 28.0  # was 70 — tight scope magnification without moving the weapon


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[fix_sniper_ads_fov] {msg}")


def find_node(editor, name: str):
    for node in editor.list_all_nodes():
        if node.get_name() == name:
            return node
    return None


def set_select_fov(editor) -> None:
    select = find_node(editor, SELECT_NODE)
    if not select:
        raise RuntimeError(f"Missing {SELECT_NODE}")

    fov_pin = select.find_input_pin(SNIPER_FOV_ENUM)
    if not fov_pin:
        raise RuntimeError(f"{SELECT_NODE} missing {SNIPER_FOV_ENUM} pin")

    current = unreal.BlueprintGraphPinLibrary.get_pin_value(fov_pin) or "?"
    if current and abs(float(current.split()[0] if " " in current else current) - SNIPER_ADS_FOV) < 0.05:
        log(f"Sniper ADS FOV already {current}")
        return

    fov_pin.set_pin_value(str(SNIPER_ADS_FOV))
    log(f"{SELECT_NODE}.{SNIPER_FOV_ENUM}: {current} -> {SNIPER_ADS_FOV}")


def verify_sniper_fov_calls(editor) -> None:
    for name in ("K2Node_CallFunction_193", "K2Node_CallFunction_60"):
        node = find_node(editor, name)
        if not node:
            log(f"WARN: missing {name}")
            continue
        pin = node.find_input_pin("TargetFOV")
        val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin) if pin else None
        log(f"VERIFY {name} TargetFOV={val}")


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    char_bp = unreal.load_asset(f"{CHAR_BP}.BP_FPCharacter")
    if not char_bp:
        raise RuntimeError("BP_FPCharacter missing")

    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
    )
    set_select_fov(editor)
    verify_sniper_fov_calls(editor)

    char_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(char_bp)
    unreal.EditorAssetLibrary.save_asset(CHAR_BP, only_if_is_dirty=False)
    log("Done — hip-fire pose unchanged; only sniper scope ADS FOV zoom increased")


main()
