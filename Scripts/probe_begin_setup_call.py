"""Find what triggers Begin Setup macro and initial weapon load."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_begin_setup_call.log")
lines = []


def log(msg: str) -> None:
    lines.append(msg)
    unreal.log(msg)


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)

for node in editor.list_all_nodes():
    name = node.get_name()
    title = str(node.get_node_title()).replace("\n", " | ")
    if "Begin Setup" in title or "BeginSetup" in title or name == "K2Node_MacroInstance_7":
        log(f"=== {name} | {title} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            direction = unreal.BlueprintGraphPinLibrary.get_pin_direction(pin)
            linked = []
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                owner = lp.get_owning_node()
                linked.append(f"{owner.get_name()}:{str(unreal.BlueprintGraphPinLibrary.get_pin_name(lp))}")
            log(f"  {'IN' if direction == unreal.EdGraphPinDirection.EGPD_INPUT else 'OUT'} {pname} -> {linked}")

# Who connects exec INTO MacroInstance_7?
for node in editor.list_all_nodes():
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) != unreal.EdGraphPinDirection.EGPD_OUTPUT:
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            owner = lp.get_owning_node()
            if owner.get_name() == "K2Node_MacroInstance_7":
                pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                log(
                    f"EXEC_IN -> MacroInstance_7 from {node.get_name()} "
                    f"{pname} | {str(node.get_node_title()).replace(chr(10),' | ')}"
                )

# Expand BeginPlay sequence chain deeper
begin = editor.find_event_node("ReceiveBeginPlay")
if begin:
    log("=== BeginPlay deep chain ===")
    visited = set()

    def walk(pin, depth=0):
        if not pin or depth > 25:
            return
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            owner = lp.get_owning_node()
            key = owner.get_name()
            if key in visited:
                continue
            visited.add(key)
            title = str(owner.get_node_title()).replace("\n", " | ")
            log(f"{'  '*depth}{key} | {title}")
            if owner.get_class().get_name() == "K2Node_ExecutionSequence":
                for p in unreal.BlueprintEditorLibrary.list_all_pins(owner):
                    pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(p))
                    if pn.startswith("then_"):
                        walk(p, depth + 1)
            elif hasattr(owner, "find_then_pin"):
                walk(owner.find_then_pin(), depth + 1)

    walk(begin.find_then_pin())

OUT.write_text("\n".join(lines))
