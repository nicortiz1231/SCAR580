import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_touch_mult_nodes.log")
if LOG.exists():
    LOG.unlink()

def log(m):
    LOG.write_text(LOG.read_text() + m + "\n" if LOG.exists() else m + "\n")

def walk_in(pin, depth=0):
    if not pin or depth > 8:
        return
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
        n = unreal.BlueprintGraphPinLibrary.get_owning_node(lp)
        log("  " * depth + f"<- {n.get_name()} | {str(n.get_node_title()).replace(chr(10),'|')}")
        for p in unreal.BlueprintEditorLibrary.list_all_pins(n):
            if unreal.BlueprintGraphPinLibrary.get_pin_direction(p) == unreal.EdGraphPinDirection.EGPD_INPUT:
                walk_in(p, depth + 1)

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)

for name in ("K2Node_PromotableOperator_28", "K2Node_PromotableOperator_29"):
    for n in editor.list_all_nodes():
        if n.get_name() != name:
            continue
        log(f"=== {name} inputs ===")
        walk_in(n.find_input_pin("A"), 0)
        walk_in(n.find_input_pin("B"), 0)
