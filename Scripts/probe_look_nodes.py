"""Dump IA_Look event graph nodes from BP_FPCharacter."""

import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_look_nodes.log")


def log(msg: str) -> None:
    with open(LOG, "a") as f:
        f.write(msg + "\n")


def scan_graph(bp, graph_name: str) -> None:
    graph = None
    for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
        if g.get_name() == graph_name:
            graph = g
            break
    if not graph:
        log(f"missing graph {graph_name}")
        return

    try:
        editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    except Exception as exc:
        log(f"{graph_name}: {exc}")
        return

    for node in editor.get_all_nodes():
        title = str(node.get_node_title())
        cls = node.get_class().get_name()
        if any(k in title for k in ("Look", "Mouse", "FreeAim", "Axis", "Controller", "Sens")) or cls in (
            "K2Node_EnhancedInputActionEvent",
            "K2Node_CallFunction",
            "K2Node_GetInputAxisKeyValue",
            "K2Node_VariableGet",
        ):
            log(f"{graph_name}: {cls} | {title}")


def main() -> None:
    open(LOG, "w").close()
    bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
    for name in ("EventGraph",):
        scan_graph(bp, name)
    log("done")


if __name__ == "__main__":
    main()
