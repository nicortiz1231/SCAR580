"""Probe exec chain from ReceiveTick Recoil node."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_tick_chain.log")
lines = []


def log(msg: str) -> None:
    lines.append(msg)
    unreal.log(msg)


def walk(editor, start_pin, depth=0, max_depth=20):
    if depth > max_depth or not start_pin:
        return
    indent = "  " * depth
    for linked in unreal.BlueprintGraphPinLibrary.list_connected_pins(start_pin):
        node = unreal.BlueprintGraphPinLibrary.get_owning_node(linked)
        if not node:
            continue
        title = str(node.get_node_title()).replace("\n", " | ")
        log(f"{indent}-> {node.get_name()} | {title}")
        pins = []
        then = node.find_then_pin()
        if then:
            pins.append(then)
        if node.get_class().get_name() == "K2Node_IfThenElse":
            else_pin = node.find_else_pin()
            if else_pin:
                pins.append(else_pin)
        if node.get_class().get_name() == "K2Node_ExecutionSequence":
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) != unreal.EdGraphPinDirection.EGPD_OUTPUT:
                    continue
                if str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin)).startswith("then_"):
                    pins.append(pin)
        for pin in pins:
            walk(editor, pin, depth + 1, max_depth)


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)
tick = editor.find_event_node("ReceiveTick")
log("From ReceiveTick:")
walk(editor, tick.find_then_pin(), 0, 24)

OUT.write_text("\n".join(lines))
