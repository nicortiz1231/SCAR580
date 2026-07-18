import unreal
import traceback
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_eventgraph_full.log")
OUT.write_text("")

def log(msg):
    with OUT.open("a") as f:
        f.write(str(msg) + "\n")

def links(pin):
    if not pin:
        return []
    try:
        return list(pin.list_connected_pins())
    except Exception:
        return list(unreal.BlueprintGraphPinLibrary.list_connected_pins(pin))

def title(node):
    return str(node.get_node_title()).replace("\n", " | ")

try:
    bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
    for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
        if g.get_name() != "EventGraph":
            continue
        ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
        all_nodes = ed.list_all_nodes()
        log(f"=== EventGraph total nodes: {len(all_nodes)} ===")

        seq = next((n for n in all_nodes if n.get_name() == "K2Node_ExecutionSequence_6"), None)
        if seq:
            log(f"Found node: {seq.get_name()} | {title(seq)}")
            log(f"  class: {seq.get_class().get_name()}")
            for pin_name in ("then", "then_0", "then_1", "then_2", "then_3", "then_4", "execute"):
                pin = seq.find_output_pin(pin_name) or seq.find_input_pin(pin_name)
                if pin:
                    ls = links(pin)
                    log(f"  found pin '{pin_name}' linked={len(ls)}")
                    for l in ls:
                        log(f"     -> {l.get_owning_node().get_name()} | {title(l.get_owning_node())}")
                else:
                    log(f"  pin '{pin_name}' not found")

        # Also dump anything referencing SCAR, Opponent, Presentation, PoseSync, Multiplayer, AddComponent
        keywords = ["SCAR", "Opponent", "Presentation", "PoseSync", "Multiplayer", "Add Component", "Spawn", "Component"]
        log("=== Nodes matching keywords ===")
        for node in all_nodes:
            t = title(node)
            if any(k.lower() in t.lower() for k in keywords):
                log(f"  {node.get_name()} | {t} | class={node.get_class().get_name()}")

    log("done")
except Exception:
    log(traceback.format_exc())
