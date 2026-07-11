"""Full IA_Modding -> modding UI exec chain."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_modding_full_chain.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(bp))


def walk_exec_from(node, depth=0, seen=None):
    if seen is None:
        seen = set()
    if depth > 30 or id(node) in seen:
        return
    seen.add(id(node))
    title = str(node.get_node_title()).replace("\n", " | ")
    lines.append(f"{'  '*depth}{node.get_name()} | {title}")
    for out in ("then", "else", "Completed"):
        pin = node.find_output_pin(out)
        if not pin:
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            if lp.get_pin_direction() != unreal.EdGraphPinDirection.EGPD_INPUT:
                continue
            walk_exec_from(lp.get_owning_node(), depth + 1, seen)


ia = next(n for n in eg.list_all_nodes() if n.get_name() == "K2Node_EnhancedInputAction_22")
lines.append("=== IA_Modding Triggered chain ===")
trig = ia.find_output_pin("Triggered")
for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(trig):
    walk_exec_from(lp.get_owning_node())

# VariableGet_106 full
lines.append("\n=== VariableGet_106 all pins ===")
vg106 = next(n for n in eg.list_all_nodes() if n.get_name() == "K2Node_VariableGet_106")
for pin in unreal.BlueprintEditorLibrary.list_all_pins(vg106):
    pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
    linked = [f"{lp.get_owning_node().get_name()}:{str(unreal.BlueprintGraphPinLibrary.get_pin_name(lp))}" for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
    lines.append(f"  {pn} -> {linked}")

# trace VariableGet_144
lines.append("\n=== VariableGet_144 chain ===")
vg144 = next(n for n in eg.list_all_nodes() if n.get_name() == "K2Node_VariableGet_144")
walk_exec_from(vg144)

# Close path VariableGet_159
lines.append("\n=== then branch (close?) from IfThenElse_27 ===")
branch = next(n for n in eg.list_all_nodes() if n.get_name() == "K2Node_IfThenElse_27")
then = branch.find_output_pin("then")
for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
    walk_exec_from(lp.get_owning_node())

# functions on character related to modding
lines.append("\n=== BP functions with Modding in graph name ===")
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if "Modding" in g.get_name() or "modding" in g.get_name().lower():
        lines.append(f"  graph {g.get_name()}")

OUT.write_text("\n".join(lines))
