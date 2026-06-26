"""Trace MacroInstance_9 play rate source."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_ads_rate4.log")
AC = "/Game/BodycamFPSKIT/Blueprints/Components/AC_ProceduralAnimation.AC_ProceduralAnimation"


def log(msg):
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(msg)


def walk_back(pin, seen=None, depth=0):
    if not pin or depth > 12:
        return
    seen = seen or set()
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
        owner = unreal.BlueprintGraphPinLibrary.get_owning_node(lp)
        if not owner:
            continue
        key = owner.get_name()
        if key in seen:
            continue
        seen.add(key)
        log(f"{'  '*depth}{key} | {str(owner.get_node_title()).replace(chr(10),'|')}")
        for out in ("AnimMovementRate", "ReturnValue", "OutputPin", "Speed"):
            p = owner.find_output_pin(out)
            if p:
                walk_back(p, seen, depth + 1)


def main():
    if LOG.exists():
        LOG.unlink()

    ac = unreal.load_asset(AC)
    eg = unreal.BlueprintGraphEditor.get_graph_editor(
        next(g for g in unreal.BlueprintEditorLibrary.list_graphs(ac) if g.get_name() == "EventGraph")
    )
    for name in ("K2Node_Knot_19", "K2Node_VariableSet_24"):
        node = next((n for n in eg.list_all_nodes() if n.get_name() == name), None)
        if not node:
            continue
        log(f"=== back from {name} ===")
        walk_back(node.find_input_pin("InputPin") or node.find_input_pin("execute"))

    mi8 = next(n for n in eg.list_all_nodes() if n.get_name() == "K2Node_MacroInstance_8")
    pr = mi8.find_input_pin("PlayRate")
    log(f"MacroInstance_8 PlayRate default before={pr.get_default_value() if pr else None}")
    log("done")


main()
