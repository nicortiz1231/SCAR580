"""Probe ReceiveTick exec fan-out."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_tick_fanout.log")
if LOG.exists():
    LOG.unlink()

def log(m):
    LOG.write_text(LOG.read_text() + m + "\n" if LOG.exists() else m + "\n")

def walk_exec(pin, depth=0):
    if not pin or depth > 20:
        return
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
        n = unreal.BlueprintGraphPinLibrary.get_owning_node(lp)
        if not n:
            continue
        log("  " * depth + f"-> {n.get_name()} | {str(n.get_node_title()).replace(chr(10),'|')}")
        then = n.find_then_pin()
        if then:
            walk_exec(then, depth + 1)
        if n.get_class().get_name() == "K2Node_IfThenElse":
            ep = n.find_else_pin()
            if ep:
                walk_exec(ep, depth + 1)
        if n.get_class().get_name() == "K2Node_ExecutionSequence":
            for p in unreal.BlueprintEditorLibrary.list_all_pins(n):
                if str(unreal.BlueprintGraphPinLibrary.get_pin_name(p)).startswith("then_"):
                    walk_exec(p, depth + 1)

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)
tick = editor.find_event_node("ReceiveTick")
log("=== From ReceiveTick ===")
walk_exec(tick.find_then_pin(), 0)
