"""Repair broken IA_Modding exec chain: VariableGet_106.then -> VariableGet_144.execute."""
import unreal
from pathlib import Path

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_modding_ui_exec.log")


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[fix_modding_exec] {msg}")


def find_node(editor, name: str):
    for node in editor.list_all_nodes():
        if node.get_name() == name:
            return node
    return None


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    bp = unreal.load_asset(BP_ASSET)
    if not bp:
        raise RuntimeError(f"Missing {BP_ASSET}")

    eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)

    vg106 = find_node(editor, "K2Node_VariableGet_106")
    vg144 = find_node(editor, "K2Node_VariableGet_144")
    if not vg106 or not vg144:
        raise RuntimeError("Missing VariableGet_106 or VariableGet_144")

    then_pin = vg106.find_output_pin("then")
    exec_pin = vg144.find_input_pin("execute")
    if not then_pin or not exec_pin:
        raise RuntimeError("Missing then/execute pins on modding chain nodes")

    for linked in unreal.BlueprintGraphPinLibrary.list_connected_pins(then_pin):
        unreal.BlueprintGraphPinLibrary.break_pin_links(linked)

    if not then_pin.try_create_connection(exec_pin):
        raise RuntimeError("Failed wiring VariableGet_106.then -> VariableGet_144.execute")

    log("Wired IA_Modding SpawnedItem getter into UI_Modding toggle chain")

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)
    log("Done — X / IA_Modding / touch X should open UI_WeaponModding again")


main()
