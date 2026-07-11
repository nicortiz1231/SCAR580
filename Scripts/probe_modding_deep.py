"""Deep trace from IA_Modding Triggered pin."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_modding_deep.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(bp))


def walk_from_pin(pin, depth=0, seen=None):
    if not pin or depth > 25:
        return
    if seen is None:
        seen = set()
    node = pin.get_owning_node()
    if id(node) in seen:
        return
    seen.add(id(node))
    title = str(node.get_node_title()).replace("\n", " | ")
    lines.append(f"{'  '*depth}{node.get_name()} | {title}")
    for out_name in ("then", "ReturnValue"):
        out = node.find_output_pin(out_name)
        if not out:
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(out):
            if lp.get_pin_direction() != unreal.EdGraphPinDirection.EGPD_INPUT:
                continue
            walk_from_pin(lp, depth + 1, seen)


ia = None
for node in eg.list_all_nodes():
    if node.get_name() == "K2Node_EnhancedInputAction_22":
        ia = node
        break

if ia:
    lines.append("=== From IA_Modding Triggered ===")
    trig = ia.find_output_pin("Triggered")
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(trig):
        walk_from_pin(lp)

    lines.append("\n=== From IA_Modding Started ===")
    started = ia.find_output_pin("Started")
    if started:
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(started):
            walk_from_pin(lp)

# trace VariableGet_106 full downstream exec
for node in eg.list_all_nodes():
    if node.get_name() != "K2Node_VariableGet_106":
        continue
    lines.append("\n=== VariableGet_106 downstream ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) != unreal.EdGraphPinDirection.EGPD_OUTPUT:
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            walk_from_pin(lp)

# find all CreateWidget for WeaponModding in all graphs
lines.append("\n=== All WeaponModding CreateWidget ===")
for graph in unreal.BlueprintEditorLibrary.list_graphs(bp):
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    for node in ed.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if node.get_class().get_name() != "K2Node_CreateWidget":
            continue
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            if str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin)) != "Class":
                continue
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            if val and "WeaponModding" in val:
                lines.append(f"  graph={graph.get_name()} node={node.get_name()} class={val}")

# UI_Modding variable set nodes
lines.append("\n=== Set UI_Modding nodes ===")
for graph in unreal.BlueprintEditorLibrary.list_graphs(bp):
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    for node in ed.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if "Set UI_Modding" in title or "Get UI_Modding" in title:
            lines.append(f"  {graph.get_name()} | {node.get_name()} | {title}")

OUT.write_text("\n".join(lines))
