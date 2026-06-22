"""Find FreeAim / Mouse axis nodes in BP_FPCharacter EventGraph."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_freeaim_nodes.log")


def log(msg: str) -> None:
    with open(LOG, "a") as f:
        f.write(msg + "\n")
    unreal.log(f"[probe_freeaim] {msg}")


def main() -> None:
    LOG.write_text("")
    bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
    eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)
    for node in editor.list_all_nodes():
        cls = node.get_class().get_name()
        t = str(node.get_node_title()).replace("\n", " | ")
        name = node.get_name()
        if any(k in t for k in ("Mouse", "FreeAim", "Horizontal", "Vertical", "Get Input Axis")):
            log(f"{name} | {cls} | {t}")
            if cls == "K2Node_CallFunction" and "FreeAim" in t:
                for pin in node.get_all_pins():
                    if pin.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT:
                        log(f"  in: {pin.get_pin_name()}")
    log("done")


main()
