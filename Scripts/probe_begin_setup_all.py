"""Search all BP graphs for Begin Setup invocation."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_begin_setup_all.log")
lines = []


def log(msg: str) -> None:
    lines.append(msg)
    unreal.log(msg)


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")

for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if "Begin Setup" not in title and "BeginSetup" not in title:
            continue
        log(f"[{g.get_name()}] {node.get_name()} | {title}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            linked = []
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                owner = lp.get_owning_node()
                linked.append(f"{owner.get_name()}:{pname}")
            if linked:
                log(f"  {pname} -> {linked}")

# Search any macro named Begin Setup
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if "Begin" in g.get_name() or "Setup" in g.get_name() or "LOAD" in g.get_name():
        log(f"GRAPH: {g.get_name()}")

# LOADSAVE graph - weapon slot setup
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if g.get_name() != "LOADSAVE":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    log("=== LOADSAVE slot sets ===")
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if "Set " in title and "Slot" in title:
            log(f"  {node.get_name()} | {title}")

OUT.write_text("\n".join(lines))
