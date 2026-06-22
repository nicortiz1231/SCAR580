"""Trace Mouse X full chain to FreeAim including sens multiply."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_mouse_sens_chain.log")
if LOG.exists():
    LOG.unlink()

def log(m):
    LOG.write_text(LOG.read_text() + m + "\n" if LOG.exists() else m + "\n")

def walk_back(pin, depth=0):
    if not pin or depth > 10:
        return
    node = unreal.BlueprintGraphPinLibrary.get_owning_node(pin)
    if node:
        log("  " * depth + f"<- {node.get_name()} | {str(node.get_node_title()).replace(chr(10),'|')} [{pin.get_pin_name()}]")
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
        walk_back(lp, depth + 1)

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)

for name in ("K2Node_GetInputAxisKeyValue_0", "K2Node_GetInputAxisKeyValue_1", "K2Node_PromotableOperator_30"):
    for n in editor.list_all_nodes():
        if n.get_name() != name:
            continue
        log(f"=== {name} ===")
        if "GetInputAxis" in name:
            walk_back(n.find_output_pin("ReturnValue"), 0)
        else:
            walk_back(n.find_input_pin("A"), 0)
            log("--- B ---")
            walk_back(n.find_input_pin("B"), 0)

freeaim = None
for n in editor.list_all_nodes():
    if n.get_name() == "K2Node_CallFunction_23":
        freeaim = n
if freeaim:
    for pname in ("HorizontalMouse", "VerticalMouse", "IsAim", "CanAim"):
        p = freeaim.find_input_pin(pname)
        log(f"FreeAim {pname}: connected={bool(p and unreal.BlueprintGraphPinLibrary.list_connected_pins(p))}")
