"""Trace IfThenElse_27 modding toggle branch."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_modding_branch.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(bp))

branch = next(n for n in eg.list_all_nodes() if n.get_name() == "K2Node_IfThenElse_27")
lines.append(f"Branch {branch.get_node_title()}")
for pin in unreal.BlueprintEditorLibrary.list_all_pins(branch):
    pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
    linked = []
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
        owner = lp.get_owning_node()
        linked.append(f"{owner.get_name()}:{pn}")
    val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
    if linked or val:
        lines.append(f"  {pn} val={val!r} linked={linked}")

# trace condition pin
cond = branch.find_input_pin("Condition")
if cond:
    stack = [(cond, 0)]
    seen = set()
    lines.append("\n=== Condition chain ===")
    while stack:
        p, depth = stack.pop()
        owner = p.get_owning_node()
        if id(owner) in seen or depth > 12:
            continue
        seen.add(id(owner))
        title = str(owner.get_node_title()).replace("\n", " | ")
        lines.append(f"{'  '*depth}{owner.get_name()} | {title}")
        for ip in unreal.BlueprintEditorLibrary.list_all_pins(owner):
            if unreal.BlueprintGraphPinLibrary.get_pin_direction(ip) != unreal.EdGraphPinDirection.EGPD_INPUT:
                continue
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(ip))
            if pn in ("self", "execute"):
                continue
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(ip):
                stack.append((lp, depth + 1))

# then branch from IfThenElse_27
then = branch.find_output_pin("then")
lines.append("\n=== then branch ===")
if then:
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
        n = lp.get_owning_node()
        lines.append(f"  {n.get_name()} | {n.get_node_title()}")

# trace from VariableGet_106 through to branch
lines.append("\n=== SpawnedItem modding path ===")
start = next(n for n in eg.list_all_nodes() if n.get_name() == "K2Node_VariableGet_106")
stack = [(start, 0)]
seen = set()
while stack:
    node, depth = stack.pop()
    if id(node) in seen or depth > 15:
        continue
    seen.add(id(node))
    title = str(node.get_node_title()).replace("\n", " | ")
    lines.append(f"{'  '*depth}{node.get_name()} | {title}")
    for out in ("then", "ReturnValue"):
        pin = node.find_output_pin(out)
        if not pin:
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            if lp.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT:
                stack.append((lp.get_owning_node(), depth + 1))

OUT.write_text("\n".join(lines))
