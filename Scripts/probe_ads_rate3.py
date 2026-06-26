"""Inspect Float Timeline macro PlayRate pins for aim transition."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_ads_rate3.log")
AC = "/Game/BodycamFPSKIT/Blueprints/Components/AC_ProceduralAnimation.AC_ProceduralAnimation"


def log(msg):
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(msg)


def pin_default(pin):
    for fn in ("get_default_value", "get_default_as_string"):
        try:
            return getattr(pin, fn)()
        except Exception:
            pass
    return "?"


def inspect_macro(editor, node_name):
    node = None
    for n in editor.list_all_nodes():
        if n.get_name() == node_name:
            node = n
            break
    if not node:
        log(f"missing {node_name}")
        return
    log(f"=== {node_name} ===")
    for pin_name in ("Play", "PlayFromStart", "PlayRate", "NewRate", "Rate"):
        pin = node.find_input_pin(pin_name)
        if not pin:
            continue
        links = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            owner = unreal.BlueprintGraphPinLibrary.get_owning_node(lp)
            links.append(owner.get_name() if owner else "?")
        log(f"  {pin_name} default={pin_default(pin)!r} links={links}")
    upd = node.find_output_pin("Update")
    if upd:
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(upd):
            owner = unreal.BlueprintGraphPinLibrary.get_owning_node(lp)
            log(f"  Update -> {owner.get_name() if owner else '?'}")


def backward_data(pin, depth=0):
    if not pin or depth > 8:
        return
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
        owner = unreal.BlueprintGraphPinLibrary.get_owning_node(lp)
        if not owner:
            continue
        log(f"{'  '*depth}rate src {owner.get_name()} | {str(owner.get_node_title()).replace(chr(10),'|')}")
        for in_name in ("AnimMovementRate", "ReturnValue", "OutputPin"):
            in_pin = owner.find_output_pin(in_name) or owner.find_input_pin(in_name)
            if in_pin and in_pin != lp:
                backward_data(in_pin, depth + 1)


def main():
    if LOG.exists():
        LOG.unlink()

    ac = unreal.load_asset(AC)
    eg = None
    for graph in unreal.BlueprintEditorLibrary.list_graphs(ac):
        if graph.get_name() == "EventGraph":
            eg = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    if not eg:
        return

    for name in (
        "K2Node_MacroInstance_6",
        "K2Node_MacroInstance_1",
        "K2Node_MacroInstance_8",
        "K2Node_MacroInstance_9",
    ):
        inspect_macro(eg, name)

    for n in eg.list_all_nodes():
        if n.get_name() == "K2Node_MacroInstance_8":
            log("=== MacroInstance_8 PlayRate backward ===")
            backward_data(n.find_input_pin("PlayRate"))
        if n.get_name() == "K2Node_Knot_28":
            log("=== Knot_28 backward ===")
            backward_data(n.find_input_pin("InputPin"))

    log("done")


main()
