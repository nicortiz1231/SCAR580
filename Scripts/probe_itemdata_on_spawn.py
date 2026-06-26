"""Check if spawned weapon gets ItemData before SpawnAttachments."""
import unreal
from pathlib import Path
OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_itemdata_on_spawn.log")
lines = []
bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(bp))
for node in editor.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    if "ItemData" not in title and "Item Data" not in title:
        continue
    if node.get_class().get_name() not in ("K2Node_VariableSet", "K2Node_CallFunction"):
        continue
    lines.append(f"{node.get_name()} | {title}")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        if pn in ("execute", "then", "self", "ItemData"):
            linked = []
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                linked.append(lp.get_owning_node().get_name())
            if linked:
                lines.append(f"  {pn} -> {linked}")
# walk back from SpawnAttachments 140 exec input
for name in ("K2Node_CallFunction_140", "K2Node_CallFunction_141"):
    for node in editor.list_all_nodes():
        if node.get_name() != name:
            continue
        lines.append(f"=== backchain {name} ===")
        stack = [(node.find_input_pin("execute"), 0)]
        while stack:
            pin, depth = stack.pop()
            if not pin or depth > 20:
                continue
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                o = lp.get_owning_node()
                lines.append(f"{'  '*depth}{o.get_name()} | {str(o.get_node_title()).replace(chr(10),' | ')}")
                for p in unreal.BlueprintEditorLibrary.list_all_pins(o):
                    if unreal.BlueprintGraphPinLibrary.get_pin_name(p) == "execute":
                        stack.append((p, depth + 1))
OUT.write_text("\n".join(lines))
