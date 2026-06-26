"""Dump Akimbo Selector macro usage on character in original."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_orig_akimbo_macro.log")
lines = []

char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
ced = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))

for node in ced.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    if "Akimbo Selector" not in title and "Akimbo Spawner" not in title:
        continue
    lines.append(f"=== {node.get_name()} | {title} ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        linked = [f"{lp.get_owning_node().get_name()}:{unreal.BlueprintGraphPinLibrary.get_pin_name(lp)}" for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
        if linked:
            lines.append(f"  {pn} -> {linked}")

# trace back from macro instance 6 exec
for name in ("K2Node_MacroInstance_6", "K2Node_MacroInstance_10", "K2Node_MacroInstance_0"):
    for node in ced.list_all_nodes():
        if node.get_name() != name:
            continue
        lines.append(f"\n=== backchain {name} ===")
        exec_in = node.find_input_pin("execute")
        if not exec_in:
            continue
        stack = [(exec_in, 0)]
        while stack:
            pin, depth = stack.pop()
            if not pin or depth > 15:
                continue
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                if lp.get_pin_direction() != unreal.EdGraphPinDirection.EGPD_OUTPUT:
                    continue
                o = lp.get_owning_node()
                lines.append(f"{'  '*depth}{o.get_name()} | {str(o.get_node_title()).replace(chr(10),' | ')}")
                for inp in unreal.BlueprintEditorLibrary.list_all_pins(o):
                    if unreal.BlueprintGraphPinLibrary.get_pin_direction(inp) == unreal.EdGraphPinDirection.EGPD_INPUT and str(unreal.BlueprintGraphPinLibrary.get_pin_name(inp)) == "execute":
                        stack.append((inp, depth + 1))

OUT.write_text("\n".join(lines))
