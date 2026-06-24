"""Increase pistol ADS pose speed only — aim timeline Play Rate, nothing else."""

import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_pistol_ads_speed.log")

AC_PROCEDURAL = "/Game/BodycamFPSKIT/Blueprints/Components/AC_ProceduralAnimation"
AIM_TIMELINE_NODE = "K2Node_MacroInstance_8"
# Stock aim Float Timeline play rate; modest bump keeps motion natural.
NEW_AIM_PLAY_RATE = 9.0


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[fix_pistol_ads_speed] {msg}")


def find_event_graph_editor(bp):
    for graph in unreal.BlueprintEditorLibrary.list_graphs(bp):
        if graph.get_name() == "EventGraph":
            return unreal.BlueprintGraphEditor.get_graph_editor(graph)
    raise RuntimeError("EventGraph not found on AC_ProceduralAnimation")


def find_node(editor, name: str):
    for node in editor.list_all_nodes():
        if node.get_name() == name:
            return node
    return None


def bump_aim_timeline_play_rate() -> bool:
    bp = unreal.load_asset(AC_PROCEDURAL)
    if not bp:
        raise RuntimeError(f"Failed to load {AC_PROCEDURAL}")

    editor = find_event_graph_editor(bp)
    aim_timeline = find_node(editor, AIM_TIMELINE_NODE)
    if not aim_timeline:
        raise RuntimeError(f"Missing {AIM_TIMELINE_NODE}")

    play_rate = aim_timeline.find_input_pin("PlayRate")
    if not play_rate:
        raise RuntimeError(f"{AIM_TIMELINE_NODE} has no PlayRate pin")

    if unreal.BlueprintGraphPinLibrary.list_connected_pins(play_rate):
        raise RuntimeError(
            f"{AIM_TIMELINE_NODE}.PlayRate is wired; revert asset before running this script"
        )

    current = unreal.BlueprintGraphPinLibrary.get_pin_value(play_rate) or "0"
    if abs(float(current) - NEW_AIM_PLAY_RATE) < 0.0001:
        log(f"{AIM_TIMELINE_NODE} PlayRate already {current}")
        return False

    play_rate.set_pin_value(str(NEW_AIM_PLAY_RATE))
    log(f"{AIM_TIMELINE_NODE} PlayRate: {current} -> {NEW_AIM_PLAY_RATE}")

    bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(AC_PROCEDURAL, only_if_is_dirty=False)
    log("Saved AC_ProceduralAnimation (aim timeline play rate only)")
    return True


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    if bump_aim_timeline_play_rate():
        log("ADS pose speed increased (aim timeline only, no other changes)")
    else:
        log("No changes needed")


main()
