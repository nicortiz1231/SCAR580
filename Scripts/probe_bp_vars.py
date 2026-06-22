"""List BP_FPCharacter member variables and FreeAim exec wiring."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_bp_vars.log")


def log(msg: str) -> None:
    with open(LOG, "a") as f:
        f.write(msg + "\n")
    unreal.log(f"[probe_vars] {msg}")


def list_pin_links(node, pin_name: str) -> None:
    pin = node.find_input_pin(pin_name) or node.find_output_pin(pin_name)
    if not pin:
        return
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
        n = unreal.BlueprintGraphPinLibrary.get_owning_node(lp)
        log(f"  {pin_name} -> {n.get_name() if n else '?'}:{lp.get_pin_name()}")


def main() -> None:
    LOG.write_text("")
    bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")

    for var in bp.new_variables:
        log(f"VAR {var.var_name} | {var.var_type.pin_category}")

    eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)

    freeaim = None
    for node in editor.list_all_nodes():
        if node.get_name() == "K2Node_CallFunction_23":
            freeaim = node
            break
    if freeaim:
        log("FreeAim exec in:")
        list_pin_links(freeaim, "execute")
        log("FreeAim HorizontalMouse:")
        list_pin_links(freeaim, "HorizontalMouse")
        log("FreeAim VerticalMouse:")
        list_pin_links(freeaim, "VerticalMouse")

    tick = editor.find_event_node("ReceiveTick")
    if tick:
        log("ReceiveTick then:")
        list_pin_links(tick, "then")

    log("done")


main()
