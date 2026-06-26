"""Probe ReceiveTick execution sequence pins."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_tick_seq.log")
lines = []


def log(msg: str) -> None:
    lines.append(msg)
    unreal.log(msg)


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)

tick = editor.find_event_node("ReceiveTick")
log(f"ReceiveTick then ->")
for linked in unreal.BlueprintGraphPinLibrary.list_connected_pins(tick.find_then_pin()):
    node = unreal.BlueprintGraphPinLibrary.get_owning_node(linked)
    log(f"  {node.get_name()} | {str(node.get_node_title()).replace(chr(10), ' | ')}")

for node in editor.list_all_nodes():
    if node.get_class().get_name() != "K2Node_ExecutionSequence":
        continue
    title = str(node.get_node_title()).replace("\n", " | ")
    log(f"SEQ {node.get_name()} | {title}")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) != unreal.EdGraphPinDirection.EGPD_OUTPUT:
            continue
        pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        if not pname.startswith("then"):
            continue
        links = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            owner = lp.get_owning_node()
            links.append(f"{owner.get_name()}:{str(owner.get_node_title()).replace(chr(10), ' | ')}")
        log(f"  {pname} -> {links}")

OUT.write_text("\n".join(lines))
