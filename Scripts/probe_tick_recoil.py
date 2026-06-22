import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_tick_recoil.log")

def log(msg):
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")

if LOG.exists():
    LOG.unlink()

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)

recoil = None
for n in editor.list_all_nodes():
    if n.get_name() == "K2Node_CallFunction_153":
        recoil = n
        break

tick = editor.find_event_node("ReceiveTick")

if recoil:
    exec_in = recoil.find_input_pin("execute")
    links = unreal.BlueprintGraphPinLibrary.list_connected_pins(exec_in)
    log(f"Recoil execute in links: {len(links)}")
    for lp in links:
        n = unreal.BlueprintGraphPinLibrary.get_owning_node(lp)
        log(f"  from {n.get_name()} | {str(n.get_node_title()).replace(chr(10),'|')}")

if tick:
    then = tick.find_then_pin()
    links = unreal.BlueprintGraphPinLibrary.list_connected_pins(then)
    log(f"Tick then links: {len(links)}")
    for lp in links:
        n = unreal.BlueprintGraphPinLibrary.get_owning_node(lp)
        log(f"  to {n.get_name()} | {str(n.get_node_title()).replace(chr(10),'|')}")

# Mouse axis -> what consumes them
for name in ("K2Node_GetInputAxisKeyValue_0", "K2Node_GetInputAxisKeyValue_1"):
    for n in editor.list_all_nodes():
        if n.get_name() != name:
            continue
        out = n.find_output_pin("ReturnValue")
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(out):
            owner = unreal.BlueprintGraphPinLibrary.get_owning_node(lp)
            log(f"{name} ReturnValue -> {owner.get_name()}:{lp.get_pin_name()}")

# FreeAim horizontal input chain
freeaim = None
for n in editor.list_all_nodes():
    if n.get_name() == "K2Node_CallFunction_23":
        freeaim = n
        break
if freeaim:
    h = freeaim.find_input_pin("HorizontalMouse")
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(h):
        owner = unreal.BlueprintGraphPinLibrary.get_owning_node(lp)
        log(f"FreeAim H -> {owner.get_name()} | {str(owner.get_node_title()).replace(chr(10),'|')}")
