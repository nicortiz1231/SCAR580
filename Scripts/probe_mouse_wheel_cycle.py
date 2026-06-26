"""Probe mouse wheel weapon cycle chain."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_mouse_wheel_cycle.log")
lines = []


def log(msg: str) -> None:
    lines.append(msg)
    unreal.log(msg)


def dump_node(editor, name):
    for node in editor.list_all_nodes():
        if node.get_name() != name:
            continue
        title = str(node.get_node_title()).replace("\n", " | ")
        log(f"=== {name} | {title} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
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
            log(f"  {dir_s} {pname}{default} -> {linked}")


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)

for name in (
    "K2Node_IfThenElse_16",
    "K2Node_IfThenElse_54",
    "K2Node_VariableSet_45",
    "K2Node_VariableGet_45",
    "K2Node_CustomEvent_13",
    "K2Node_MacroInstance_11",
    "K2Node_IfThenElse_22",
    "K2Node_IfThenElse_4",
    "K2Node_IfThenElse_32",
):
    dump_node(editor, name)

# IA_MouseWheel asset type
ia = unreal.load_asset("/Game/BodycamFPSKIT/Input/Actions/IA_MouseWheel.IA_MouseWheel")
if ia:
    try:
        log(f"IA_MouseWheel value_type={ia.get_editor_property('value_type')}")
    except Exception as exc:
        log(f"IA_MouseWheel props ERR {exc}")

OUT.write_text("\n".join(lines))
