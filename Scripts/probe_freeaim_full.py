"""Full probe: FreeAim exec drivers, IsAim, CanAim, mouse/tick wiring."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_freeaim_full.log")


def log(msg: str) -> None:
    with open(LOG, "a") as f:
        f.write(msg + "\n")
    unreal.log(f"[probe_full] {msg}")


def trace_exec_back(node, depth=0, seen=None):
    if seen is None:
        seen = set()
    if not node or node.get_name() in seen or depth > 25:
        return
    seen.add(node.get_name())
    title = str(node.get_node_title()).replace("\n", " | ")
    log("  " * depth + f"EXEC<- {node.get_name()} | {title}")
    pin = node.find_input_pin("execute")
    if not pin:
        return
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
        n = unreal.BlueprintGraphPinLibrary.get_owning_node(lp)
        trace_exec_back(n, depth + 1, seen)


def trace_exec_forward(node, depth=0, seen=None):
    if seen is None:
        seen = set()
    if not node or node.get_name() in seen or depth > 25:
        return
    seen.add(node.get_name())
    title = str(node.get_node_title()).replace("\n", " | ")
    log("  " * depth + f"EXEC-> {node.get_name()} | {title}")
    then = node.find_then_pin()
    if not then:
        return
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
        n = unreal.BlueprintGraphPinLibrary.get_owning_node(lp)
        trace_exec_forward(n, depth + 1, seen)


def main() -> None:
    LOG.write_text("")
    bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
    eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)

    for name in ("IsAim", "CanAim", "BODYCAM"):
        if name in unreal.BlueprintEditorLibrary.list_member_variable_names(bp):
            log(f"VAR {name} exists")

    # All events that have exec out
    for node in editor.list_all_nodes():
        cls = node.get_class().get_name()
        if cls not in ("K2Node_Event", "K2Node_CustomEvent", "K2Node_EnhancedInputAction", "K2Node_InputAction"):
            continue
        title = str(node.get_node_title()).replace("\n", " | ")
        then = node.find_then_pin()
        links = unreal.BlueprintGraphPinLibrary.list_connected_pins(then) if then else []
        if links or "Tick" in title or "Touch" in title or "Aim" in title:
            log(f"EVENT {node.get_name()} | {title} | exec_out={len(links)}")

    freeaim = None
    for node in editor.list_all_nodes():
        if node.get_name() == "K2Node_CallFunction_23":
            freeaim = node
            break

    if freeaim:
        log("=== Backward exec into FreeAim ===")
        trace_exec_back(freeaim, 0)
        log("=== Forward exec from FreeAim ===")
        trace_exec_forward(freeaim, 0)

    # Find anything calling FreeAim or with FreeAim in title
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if "FreeAim" in title and node.get_class().get_name() == "K2Node_CallFunction":
            log(f"FREEAIM_NODE {node.get_name()} | {title}")
            trace_exec_back(node, 0)

    # Mobile drag marker
    for node in editor.list_all_nodes():
        if node.get_class().get_name() != "K2Node_Comment":
            continue
        try:
            text = str(node.get_editor_property("node_comment"))
        except Exception:
            continue
        if "Mobile" in text and "FreeAim" in text:
            log(f"MARKER: {text}")

    # Check ReceiveTick
    tick = editor.find_event_node("ReceiveTick")
    if tick:
        log("=== ReceiveTick forward ===")
        trace_exec_forward(tick, 0)

    log("done")


main()
