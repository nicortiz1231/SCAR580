"""Fix sniper ADS scope clipping: lower near clip + pull eyepiece closer."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_sniper_ads_noclip.log")
CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
SNIPER_PATH = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper"
ENGINE_INI = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Config/DefaultEngine.ini")

# Lower near clip = geometry closer to camera stays visible (must stay below AimDistance).
AIM_DISTANCE = 2.5
ADS_NEAR_CLIP = "0.8"
HIP_NEAR_CLIP = "1.0"
ENGINE_NEAR_CLIP = "1.000000"


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[sniper_ads_noclip] {msg}")


def set_aim_distance(sniper_bp) -> None:
    cdo = unreal.get_default_object(sniper_bp.generated_class())
    current = float(cdo.get_editor_property("AimDistanceFromCamera"))
    cdo.set_editor_property("AimDistanceFromCamera", AIM_DISTANCE)
    sniper_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(sniper_bp)
    unreal.EditorAssetLibrary.save_asset(SNIPER_PATH, only_if_is_dirty=False)
    log(f"AimDistanceFromCamera {current} -> {AIM_DISTANCE}")


def update_near_clip_cmds(char_bp) -> None:
    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
    )
    ads_values = {"4.5", "5.0", "5"}
    hip_values = {"2.5", "3.25", "3.250000"}
    ads_updated = hip_updated = 0

    for node in editor.list_all_nodes():
        if "ExecuteConsoleCommand" not in str(node.get_node_title()):
            continue
        pin = node.find_input_pin("Command")
        if not pin:
            continue
        val = str(unreal.BlueprintGraphPinLibrary.get_pin_value(pin) or "")
        if "SetNearClipPlane" not in val:
            continue
        try:
            clip = val.split()[-1]
        except IndexError:
            continue

        if clip in ads_values:
            pin.set_pin_value(f"r.SetNearClipPlane {ADS_NEAR_CLIP}")
            ads_updated += 1
        elif clip in hip_values:
            pin.set_pin_value(f"r.SetNearClipPlane {HIP_NEAR_CLIP}")
            hip_updated += 1

    log(f"ADS near clip cmds updated: {ads_updated} -> {ADS_NEAR_CLIP}")
    log(f"Hip near clip cmds updated: {hip_updated} -> {HIP_NEAR_CLIP}")


def update_engine_near_clip() -> None:
    text = ENGINE_INI.read_text()
    import re

    new_text, n = re.subn(
        r"(NearClipPlane=)[0-9.]+",
        rf"\g<1>{ENGINE_NEAR_CLIP}",
        text,
        count=1,
    )
    if n:
        ENGINE_INI.write_text(new_text)
        log(f"DefaultEngine.ini NearClipPlane -> {ENGINE_NEAR_CLIP}")
    else:
        log("WARN: NearClipPlane not found in DefaultEngine.ini")


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    sniper_bp = unreal.load_asset(f"{SNIPER_PATH}.BP_Weapon_Sniper")
    char_bp = unreal.load_asset(f"{CHAR_BP}.BP_FPCharacter")
    if not sniper_bp or not char_bp:
        raise RuntimeError("Missing sniper or character blueprint")

    set_aim_distance(sniper_bp)
    update_near_clip_cmds(char_bp)
    update_engine_near_clip()

    char_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(char_bp)
    unreal.EditorAssetLibrary.save_asset(CHAR_BP, only_if_is_dirty=False)
    log("Done — closer ADS with lower near clip to prevent scope mesh clipping")


main()
