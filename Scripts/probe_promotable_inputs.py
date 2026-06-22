import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_promotable_inputs.log")
if LOG.exists():
    LOG.unlink()

def log(m):
    LOG.write_text(LOG.read_text() + m + "\n" if LOG.exists() else m + "\n")

def src(pin):
    if not pin:
        return
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
        n = unreal.BlueprintGraphPinLibrary.get_owning_node(lp)
        log(f"  {pin.get_pin_name()} <- {n.get_name()} | {str(n.get_node_title()).replace(chr(10),'|')}")

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)

for name in ("K2Node_PromotableOperator_30", "K2Node_PromotableOperator_31"):
    for n in editor.list_all_nodes():
        if n.get_name() != name:
            continue
        log(f"=== {name} ===")
        src(n.find_input_pin("A"))
        src(n.find_input_pin("B"))
