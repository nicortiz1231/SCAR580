"""Find callers of SpawnAttachments and BeginPlay item init."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_spawnatt_callers.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if "SpawnAttachments" in title and node.get_class().get_name() == "K2Node_CallFunction":
            lines.append(f"CALL [{g.get_name()}] {node.get_name()} | {title}")
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                if pname == "execute":
                    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                        owner = lp.get_owning_node()
                        lines.append(f"  exec from {owner.get_name()} | {str(owner.get_node_title()).replace(chr(10),' | ')}")

# EventGraph BeginPlay chain
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if g.get_name() != "EventGraph":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    begin = editor.find_event_node("ReceiveBeginPlay")
    if not begin:
        continue
    lines.append("=== Item BeginPlay ===")
    stack = [(begin.find_then_pin(), 0)]
    while stack:
        pin, depth = stack.pop()
        if not pin or depth > 15:
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            owner = lp.get_owning_node()
            title = str(owner.get_node_title()).replace("\n", " | ")
            lines.append(f"{'  '*depth}{owner.get_name()} | {title}")
            if hasattr(owner, "find_then_pin"):
                stack.append((owner.find_then_pin(), depth + 1))

# SpawnAttachments event graph - what does it do
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if g.get_name() != "SpawnAttachments":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append("=== SpawnAttachments graph nodes ===")
    for node in editor.list_all_nodes():
        lines.append(f"  {node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')}")

OUT.write_text("\n".join(lines))
