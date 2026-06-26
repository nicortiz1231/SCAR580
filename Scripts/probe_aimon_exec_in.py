"""Find exec wired into AIMOn/AIMOff function execute pins."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_aimon_exec_in.log")
lines = []

char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))

for target in ("K2Node_CallFunction_56", "K2Node_CallFunction_379"):
    for node in eg.list_all_nodes():
        if node.get_name() != target:
            continue
        exec_in = node.find_input_pin("execute")
        lines.append(f"\n=== {target} execute inputs ===")
        if not exec_in:
            lines.append("  NO execute pin")
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(exec_in):
            o = lp.get_owning_node()
            lines.append(f"  <- {o.get_name()} | {str(o.get_node_title()).replace(chr(10),' | ')}")

# IA_Aim enhanced input
for node in eg.list_all_nodes():
    if "IA_Aim" not in str(node.get_node_title()):
        continue
    lines.append(f"\n=== {node.get_name()} IA_Aim ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        if pn not in ("Started", "Triggered", "Completed", "Canceled"):
            continue
        linked = [f"{lp.get_owning_node().get_name()}|{str(lp.get_owning_node().get_node_title()).replace(chr(10),' ')[:30]}" for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
        lines.append(f"  {pn} -> {linked}")

OUT.write_text("\n".join(lines))
