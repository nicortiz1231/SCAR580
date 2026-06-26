"""Find Aim() function graph and compare original vs SCAR sniper scope params."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_aim_function.log")
lines = []

char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for g in unreal.BlueprintEditorLibrary.list_graphs(char):
    if g.get_name() != "Aim":
        continue
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append(f"=== Character Aim graph ({len(ed.list_all_nodes())} nodes) ===")
    for node in ed.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        lines.append(f"  {node.get_name()} | {title}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            if val:
                lines.append(f"    {pn}={val}")

ac = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Components/AC_ProceduralAnimation.AC_ProceduralAnimation")
for g in unreal.BlueprintEditorLibrary.list_graphs(ac):
    if "Aim" not in g.get_name():
        continue
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append(f"\n=== AC graph {g.get_name()} ({len(ed.list_all_nodes())} nodes) ===")
    for node in ed.list_all_nodes()[:30]:
        lines.append(f"  {node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')}")

# trace CallFunction_128 target class
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))
for node in eg.list_all_nodes():
    if node.get_name() != "K2Node_CallFunction_128":
        continue
    lines.append(f"\n=== CallFunction_128 class ===")
    try:
        lines.append(f"  {node.get_class().get_name()}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            if val:
                lines.append(f"  {pn}={val}")
    except Exception as exc:
        lines.append(f"  err={exc}")

OUT.write_text("\n".join(lines))
