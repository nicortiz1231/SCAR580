"""Trace post-spawn equip chain for attachments and ammo."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_post_spawn.log")
lines = []


def walk_exec(editor, start_name: str, depth: int = 0, max_depth: int = 12) -> None:
    for node in editor.list_all_nodes():
        if node.get_name() != start_name:
            continue
        title = str(node.get_node_title()).replace("\n", " | ")
        lines.append(f"{'  '*depth}{start_name} | {title}")
        pins = []
        if hasattr(node, "find_then_pin"):
            then = node.find_then_pin()
            if then:
                pins.append(then)
        if node.get_class().get_name() == "K2Node_IfThenElse":
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                if pn in ("then", "else"):
                    pins.append(pin)
        for pin in pins:
            if depth >= max_depth:
                continue
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                owner = lp.get_owning_node()
                walk_exec(editor, owner.get_name(), depth + 1, max_depth)
        return


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)

lines.append("=== Valid spawn chain ===")
walk_exec(editor, "K2Node_VariableSet_19")

lines.append("=== Fallback spawn chain ===")
walk_exec(editor, "K2Node_VariableSet_15")

# SpawnAttachments on item base
item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    if g.get_name() != "EventGraph":
        continue
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in ed.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if "SpawnAttachments" in title:
            lines.append(f"ITEM {node.get_name()} | {title}")

OUT.write_text("\n".join(lines))
