"""Pull sniper ADS eyepiece much closer — AimDistanceFromCamera only (hip-fire unchanged)."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_sniper_ads_close.log")
CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
SNIPER_PATH = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper"
AIM_ON_EVENT = "K2Node_CustomEvent_16"
AIM_OFF_EVENT = "K2Node_CustomEvent_19"

# Original Bodycam was 5.0; clip fixes pushed to 8.0+. Lower = eyepiece fills screen.
AIM_DISTANCE = 3.5
ADS_NEAR_CLIP = "5.0"
HIP_NEAR_CLIP = "2.5"


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[sniper_ads_close] {msg}")


def find_node(editor, name: str):
    for node in editor.list_all_nodes():
        if node.get_name() == name:
            return node
    return None


def update_near_clip_cmds(char_bp) -> None:
    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
    )
    updated = 0
    for node in editor.list_all_nodes():
        if "ExecuteConsoleCommand" not in str(node.get_node_title()):
            continue
        pin = node.find_input_pin("Command")
        if not pin:
            continue
        val = str(unreal.BlueprintGraphPinLibrary.get_pin_value(pin) or "")
        if "SetNearClipPlane 4.5" in val:
            pin.set_pin_value(f"r.SetNearClipPlane {ADS_NEAR_CLIP}")
            updated += 1
            log(f"ADS near clip -> {ADS_NEAR_CLIP}")
        elif "SetNearClipPlane 5.0" in val and AIM_ON_EVENT in str(node):
            pass  # already set
    if updated == 0:
        log("Near-clip cmd already at target or not found (ok if unchanged)")


def set_aim_distance(sniper_bp) -> None:
    cdo = unreal.get_default_object(sniper_bp.generated_class())
    current = float(cdo.get_editor_property("AimDistanceFromCamera"))
    cdo.set_editor_property("AimDistanceFromCamera", AIM_DISTANCE)
    sniper_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(sniper_bp)
    unreal.EditorAssetLibrary.save_asset(SNIPER_PATH, only_if_is_dirty=False)
    log(f"AimDistanceFromCamera {current} -> {AIM_DISTANCE}")


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    sniper_bp = unreal.load_asset(f"{SNIPER_PATH}.BP_Weapon_Sniper")
    char_bp = unreal.load_asset(f"{CHAR_BP}.BP_FPCharacter")
    if not sniper_bp or not char_bp:
        raise RuntimeError("Missing sniper or character blueprint")

    set_aim_distance(sniper_bp)
    update_near_clip_cmds(char_bp)

    char_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(char_bp)
    unreal.EditorAssetLibrary.save_asset(CHAR_BP, only_if_is_dirty=False)
    log("Done — ADS pulls weapon closer; hip-fire pose unchanged")


main()
