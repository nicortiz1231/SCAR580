"""Find IA_Look and GetInputAxisKeyValue nodes in BP_FPCharacter graphs."""

import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_look_graph.log")


def log(msg: str) -> None:
    with open(LOG, "a") as f:
        f.write(msg + "\n")
    unreal.log(f"[probe_look_graph] {msg}")


def scan_graph(graph) -> None:
    gname = graph.get_name()
    try:
        editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    except Exception as exc:
        log(f"{gname}: no editor {exc}")
        return
    for node in editor.get_all_nodes():
        cls = node.get_class().get_name()
        title = str(node.get_node_title())
        blob = f"{cls} | {title}"
        if any(
            k in blob
            for k in (
                "IA_Look",
                "Look",
                "MouseX",
                "MouseY",
                "Mouse2D",
                "GetInputAxisKeyValue",
                "AddControllerYaw",
                "AddControllerPitch",
                "FreeAim",
                "MouseSens",
            )
        ):
            log(f"{gname}: {blob}")
            try:
                for pin in node.get_all_pins():
                    pname = pin.get_pin_name()
                    if pname in (
                        "ActionValue",
                        "AxisKey",
                        "InputAxisKey",
                        "Val",
                        "Yaw",
                        "Pitch",
                    ):
                        conns = pin.get_linked_to()
                        if conns:
                            log(
                                f"  pin {pname} -> "
                                + ", ".join(
                                    f"{c.get_owning_node().get_class().get_name()}:{c.get_owning_node().get_node_title()}"
                                    for c in conns
                                )
                            )
            except Exception:
                pass


def main() -> None:
    open(LOG, "w").close()
    bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
    for graph in unreal.BlueprintEditorLibrary.list_graphs(bp):
        scan_graph(graph)
    log("done")


if __name__ == "__main__":
    main()
