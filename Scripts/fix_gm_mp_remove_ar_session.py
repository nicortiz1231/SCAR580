"""Remove Start AR Session from GM_SCAR_AR_Multiplayer BeginPlay (breaks Mac editor PIE)."""
import unreal
from pathlib import Path

LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_gm_mp_remove_ar_session.log")
GM_MP = "/Game/SCAR580/Blueprints/GameModes/GM_SCAR_AR_Multiplayer"


def log(msg: str) -> None:
    text = (LOG_PATH.read_text() + msg + "\n") if LOG_PATH.exists() else (msg + "\n")
    LOG_PATH.write_text(text)
    unreal.log(f"[fix_gm_mp_remove_ar_session] {msg}")


def node_is_start_ar_session(node) -> bool:
    if node.get_class().get_name() != "K2Node_CallFunction":
        return False
    fn_ref = str(node.get_editor_property("function_reference"))
    return "StartARSession" in fn_ref


def main() -> None:
    bp = unreal.load_asset(f"{GM_MP}.GM_SCAR_AR_Multiplayer")
    if not bp:
        raise RuntimeError(f"Missing {GM_MP}")

    event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)
    removed = 0

    for node in list(event_graph.get_editor_property("nodes")):
        if not node_is_start_ar_session(node):
            continue
        editor.remove_node(node)
        removed += 1
        log(f"Removed Start AR Session node {node.get_name()}")

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(GM_MP, only_if_is_dirty=False)
    log(f"Done. Removed {removed} Start AR Session node(s).")


if __name__ == "__main__":
    main()
