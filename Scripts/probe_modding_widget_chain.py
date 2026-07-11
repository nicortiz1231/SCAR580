"""Trace CreateWidget_2 / UI_Modding toggle chain."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_modding_widget_chain.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(bp))


def walk_exec_backwards(target_name, max_up=15):
    target = None
    for node in eg.list_all_nodes():
        if node.get_name() == target_name:
            target = node
            break
    if not target:
        lines.append(f"MISSING {target_name}")
        return
    lines.append(f"=== exec into {target_name} | {target.get_node_title()} ===")
    stack = [(target, 0)]
    seen = set()
    while stack:
        node, depth = stack.pop()
        if depth > max_up or id(node) in seen:
            continue
        seen.add(id(node))
        title = str(node.get_node_title()).replace("\n", " | ")
        lines.append(f"{'  '*depth}<- {node.get_name()} | {title}")
        exec_in = node.find_input_pin("execute")
        if not exec_in:
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(exec_in):
            walk_exec_backwards_node = lp.get_owning_node()
            stack.append((walk_exec_backwards_node, depth + 1))


def walk_exec_forwards(start_name, max_depth=20):
    start = None
    for node in eg.list_all_nodes():
        if node.get_name() == start_name:
            start = node
            break
    if not start:
        return
    lines.append(f"\n=== exec from {start_name} ===")
    stack = [(start, 0)]
    seen = set()
    while stack:
        node, depth = stack.pop()
        if depth > max_depth or id(node) in seen:
            continue
        seen.add(id(node))
        title = str(node.get_node_title()).replace("\n", " | ")
        lines.append(f"{'  '*depth}{node.get_name()} | {title}")
        then = node.find_output_pin("then")
        if not then:
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
            if lp.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT:
                stack.append((lp.get_owning_node(), depth + 1))


for name in ("K2Node_CreateWidget_2", "K2Node_VariableSet_23", "K2Node_VariableGet_12", "K2Node_VariableGet_106"):
    node = next((n for n in eg.list_all_nodes() if n.get_name() == name), None)
    if not node:
        continue
    lines.append(f"\n=== pins {name} | {node.get_node_title()} ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        d = unreal.BlueprintGraphPinLibrary.get_pin_direction(pin)
        dir_s = "IN" if d == unreal.EdGraphPinDirection.EGPD_INPUT else "OUT"
        val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
        linked = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            owner = lp.get_owning_node()
            linked.append(f"{owner.get_name()}:{str(unreal.BlueprintGraphPinLibrary.get_pin_name(lp))}")
        if linked or val:
            lines.append(f"  {dir_s} {pn} val={val!r} -> {linked}")

walk_exec_backwards("K2Node_CreateWidget_2")
walk_exec_forwards("K2Node_CreateWidget_2")

# branch from VariableGet_106 - find macro/branch using UI_Modding validity
for node in eg.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    if node.get_name() in ("K2Node_MacroInstance_4", "K2Node_MacroInstance_5", "K2Node_IfThenElse_8", "K2Node_IfThenElse_9"):
        lines.append(f"\n=== candidate {node.get_name()} | {title} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
            if linked:
                lines.append(f"  {pn} -> {linked}")

OUT.write_text("\n".join(lines))
