"""Trace data pins from GetInputAxisKeyValue_0 to FreeAim HorizontalMouse."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_mouse_to_freeaim_chain.log")
if LOG.exists():
    LOG.unlink()


def log(msg):
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")


def trace_back(editor, pin, depth=0, max_depth=12):
    if not pin or depth > max_depth:
        return
    node = unreal.BlueprintGraphPinLibrary.get_owning_node(pin)
    indent = "  " * depth
    if node:
        log(f"{indent}<- {node.get_name()} | {str(node.get_node_title()).replace(chr(10),'|')} : {pin.get_pin_name()}")
    for linked in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
        owner = unreal.BlueprintGraphPinLibrary.get_owning_node(linked)
        if not owner:
            continue
        out_pins = []
        for candidate in unreal.BlueprintEditorLibrary.list_all_pins(owner):
            if unreal.BlueprintGraphPinLibrary.get_pin_direction(candidate) != unreal.EdGraphPinDirection.EGPD_OUTPUT:
                continue
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(candidate):
                if lp == pin:
                    out_pins.append(candidate)
        for op in out_pins:
            trace_back(editor, op, depth + 1, max_depth)


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)

freeaim = None
for n in editor.list_all_nodes():
    if n.get_name() == "K2Node_CallFunction_23":
        freeaim = n
        break

if freeaim:
    h = freeaim.find_input_pin("HorizontalMouse")
    v = freeaim.find_input_pin("VerticalMouse")
    log("=== Backward from FreeAim HorizontalMouse ===")
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(h):
        trace_back(editor, lp, 0)
    log("=== Backward from FreeAim VerticalMouse ===")
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(v):
        trace_back(editor, lp, 0)

mouse_x = None
for n in editor.list_all_nodes():
    if n.get_name() == "K2Node_GetInputAxisKeyValue_0":
        mouse_x = n
        break
if mouse_x:
    log("=== Forward from Mouse X ReturnValue ===")
    out = mouse_x.find_output_pin("ReturnValue")
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(out):
        owner = unreal.BlueprintGraphPinLibrary.get_owning_node(lp)
        log(f"  -> {owner.get_name()} | {str(owner.get_node_title()).replace(chr(10),'|')}")
