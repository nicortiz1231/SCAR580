"""Verify IsAim is set by LeftShift / AIMOn path."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_isaim.log")
if LOG.exists():
    LOG.unlink()

def log(m):
    LOG.write_text(LOG.read_text() + m + "\n" if LOG.exists() else m + "\n")

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)

for name in ("K2Node_CustomEvent_16", "K2Node_CustomEvent_19", "K2Node_CallFunction_56", "K2Node_CallFunction_379"):
    n = None
    for node in editor.list_all_nodes():
        if node.get_name() == name:
            n = node
            break
    if not n:
        continue
    title = str(n.get_node_title()).replace("\n", " | ")
    log(f"{name} | {title}")
    then = n.find_then_pin()
    if then:
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
            owner = unreal.BlueprintGraphPinLibrary.get_owning_node(lp)
            log(f"  then -> {owner.get_name()} | {str(owner.get_node_title()).replace(chr(10),'|')}")

# Find sets to IsAim
for node in editor.list_all_nodes():
    if node.get_class().get_name() != "K2Node_VariableSet":
        continue
    pin = node.find_input_pin("IsAim")
    if pin:
        log(f"Set IsAim: {node.get_name()}")

# EnhancedInput IA_Aim
for node in editor.list_all_nodes():
    if "IA_Aim" not in str(node.get_node_title()):
        continue
    log(f"IA_Aim node {node.get_name()}")
    for pin_name in ("Started", "Triggered", "Completed", "Canceled"):
        p = node.find_output_pin(pin_name)
        if not p:
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(p):
            owner = unreal.BlueprintGraphPinLibrary.get_owning_node(lp)
            log(f"  {pin_name} -> {owner.get_name()} | {str(owner.get_node_title()).replace(chr(10),'|')}")
