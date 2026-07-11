"""Trace IA_Modding and CreateHUD wiring on BP_FPCharacter."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_modding_flow.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(bp))


def walk_exec(node, depth=0, seen=None, max_depth=20):
    if seen is None:
        seen = set()
    if depth > max_depth or id(node) in seen:
        return
    seen.add(id(node))
    title = str(node.get_node_title()).replace("\n", " | ")
    lines.append(f"{'  '*depth}{node.get_name()} | {title}")
    then = node.find_output_pin("then")
    if not then:
        return
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
        if lp.get_pin_direction() != unreal.EdGraphPinDirection.EGPD_INPUT:
            continue
        walk_exec(lp.get_owning_node(), depth + 1, seen, max_depth)


for node in eg.list_all_nodes():
    if node.get_name() == "K2Node_EnhancedInputAction_22":
        lines.append("=== IA_Modding chain ===")
        walk_exec(node)
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if pname in ("Triggered", "Started", "Completed"):
                linked = []
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                    linked.append(lp.get_owning_node().get_name())
                if linked:
                    lines.append(f"  pin {pname} -> {linked}")

for graph in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if graph.get_name() != "CreateHUD":
        continue
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    lines.append("\n=== CreateHUD nodes ===")
    for node in ed.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if any(k in title for k in ("Create Widget", "UI_", "Modding", "Add to Viewport", "UI_Modding", "WeaponModding")):
            lines.append(f"  {node.get_name()} | {title}")
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                if pn in ("Class", "ReturnValue", "OwningPlayer"):
                    val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                    linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
                    lines.append(f"    {pn} default={val!r} linked={linked}")

# CloseModding
for node in eg.list_all_nodes():
    if "CloseModding" not in str(node.get_node_title()):
        continue
    lines.append(f"\n=== CloseModding {node.get_name()} ===")
    walk_exec(node, max_depth=12)

OUT.write_text("\n".join(lines))
