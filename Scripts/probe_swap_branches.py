"""Probe primary/secondary swap branch conditions."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_swap_branches.log")
lines = []


def log(msg: str) -> None:
    lines.append(msg)
    unreal.log(msg)


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)

TARGETS = {
    "K2Node_IfThenElse_4",
    "K2Node_IfThenElse_32",
    "K2Node_IfThenElse_35",
    "K2Node_IfThenElse_16",
}


def dump_node(node):
    name = node.get_name()
    title = str(node.get_node_title()).replace("\n", " | ")
    log(f"=== {name} | {title} ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pin_name = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        direction = unreal.BlueprintGraphPinLibrary.get_pin_direction(pin)
        dir_s = "IN" if direction == unreal.EdGraphPinDirection.EGPD_INPUT else "OUT"
        linked = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            owner = lp.get_owning_node()
            linked.append(f"{owner.get_name()}:{str(unreal.BlueprintGraphPinLibrary.get_pin_name(lp))}")
        default = ""
        try:
            default = f" default={pin.get_default_as_string()!r}"
        except Exception:
            pass
        log(f"  {dir_s} {pin_name}{default} -> {linked}")


for node in editor.list_all_nodes():
    if node.get_name() in TARGETS:
        dump_node(node)

OUT.write_text("\n".join(lines))
