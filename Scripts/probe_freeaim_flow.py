"""Find what drives FreeAim exec chain and ReceiveTick wiring."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_freeaim_flow.log")


def log(msg: str) -> None:
    with open(LOG, "a") as f:
        f.write(msg + "\n")
    unreal.log(f"[probe_flow] {msg}")


def trace_exec_forward(node, depth=0, seen=None):
    if seen is None:
        seen = set()
    if not node or node.get_name() in seen or depth > 15:
        return
    seen.add(node.get_name())
    title = str(node.get_node_title()).replace("\n", " | ")
    log("  " * depth + f"{node.get_name()} | {title}")
    then = node.find_then_pin()
    if not then:
        return
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
        n = unreal.BlueprintGraphPinLibrary.get_owning_node(lp)
        trace_exec_forward(n, depth + 1, seen)


def trace_exec_backward(node, depth=0, seen=None):
    if seen is None:
        seen = set()
    if not node or node.get_name() in seen or depth > 15:
        return
    seen.add(node.get_name())
    title = str(node.get_node_title()).replace("\n", " | ")
    log("  " * depth + f"{node.get_name()} | {title}")
    exec_in = node.find_input_pin("execute")
    if not exec_in:
        return
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(exec_in):
        n = unreal.BlueprintGraphPinLibrary.get_owning_node(lp)
        trace_exec_backward(n, depth + 1, seen)


def main() -> None:
    LOG.write_text("")
    bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
    eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)

    shake = None
    freeaim = None
    for node in editor.list_all_nodes():
        if node.get_name() == "K2Node_CallFunction_34":
            shake = node
        if node.get_name() == "K2Node_CallFunction_23":
            freeaim = node

    if shake:
        log("=== Backward from Camera Shake execute ===")
        trace_exec_backward(shake, 0)
        log("=== Forward from Camera Shake then ===")
        trace_exec_forward(shake, 0)

    if freeaim:
        log("=== Forward from FreeAim then (for SET insertion) ===")
        trace_exec_forward(freeaim, 0)

    tick = editor.find_event_node("ReceiveTick")
    if tick:
        log("=== Forward from ReceiveTick ===")
        trace_exec_forward(tick, 0)

    log("done")


main()
