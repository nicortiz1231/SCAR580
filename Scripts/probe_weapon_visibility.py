"""Diagnose invisible weapons: spawn chain, equip, mesh visibility."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_weapon_visibility.log")
lines = []


def w(s=""):
    lines.append(s)


def dump_node(editor, name):
    for node in editor.list_all_nodes():
        if node.get_name() != name:
            continue
        w(f"=== {name} | {str(node.get_node_title()).replace(chr(10),' | ')} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            linked = [f"{lp.get_owning_node().get_name()}:{unreal.BlueprintGraphPinLibrary.get_pin_name(lp)}" for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            if linked or val:
                w(f"  {pn} -> {linked or val}")
        return True
    return False


def walk_exec(editor, start_name, max_depth=25):
    start = None
    for node in editor.list_all_nodes():
        if node.get_name() == start_name:
            start = node
            break
    if not start:
        w(f"MISSING {start_name}")
        return
    w(f"\n=== Exec chain from {start_name} ===")
    then = start.find_output_pin("then")
    stack = [(then, 0)]
    seen = set()
    while stack:
        pin, depth = stack.pop()
        if not pin or depth > max_depth:
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            if lp.get_pin_direction() != unreal.EdGraphPinDirection.EGPD_INPUT:
                continue
            o = lp.get_owning_node()
            if id(o) in seen:
                continue
            seen.add(id(o))
            w(f"{'  '*depth}{o.get_name()} | {str(o.get_node_title()).replace(chr(10),' | ')}")
            nxt = o.find_output_pin("then")
            if nxt:
                stack.append((nxt, depth + 1))


char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
ed = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))

for name in (
    "K2Node_SpawnActorFromClass_1", "K2Node_VariableSet_15",
    "K2Node_CallFunction_157", "K2Node_CallFunction_212", "K2Node_CallFunction_141",
    "K2Node_CallFunction_140", "K2Node_VariableGet_83", "K2Node_VariableGet_133",
    "K2Node_CallFunction_46", "K2Node_CallFunction_17",
):
    dump_node(ed, name)

walk_exec(ed, "K2Node_VariableSet_15")
walk_exec(ed, "K2Node_CallFunction_141")

# BeginSetup macro on BeginPlay
for node in ed.list_all_nodes():
    if node.get_name() == "K2Node_MacroInstance_7":
        w("\n=== Begin Setup macro ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
            if linked:
                w(f"  {pn} -> {linked}")

# HandsSlot construct
for g in unreal.BlueprintEditorLibrary.list_graphs(char):
    if g.get_name() != "BeginSetup":
        continue
    ged = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in ged.list_all_nodes():
        if node.get_name() != "K2Node_GenericCreateObject_2":
            continue
        w("\n=== HandsSlot construct ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            if val:
                w(f"  {pname}={val}")

OUT.write_text("\n".join(lines))
