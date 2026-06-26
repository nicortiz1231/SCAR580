"""Trace exec flow after character SpawnAttachments 140/141."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_post_spawnatt_char.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(bp))


def walk(node, depth=0, seen=None):
    if seen is None:
        seen = set()
    if depth > 25 or id(node) in seen:
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
        walk(lp.get_owning_node(), depth + 1, seen)


for name in ("K2Node_CallFunction_140", "K2Node_CallFunction_141"):
    node = None
    for n in eg.list_all_nodes():
        if n.get_name() == name:
            node = n
            break
    if not node:
        lines.append(f"MISSING {name}")
        continue
    lines.append(f"=== chain from {name} ===")
    walk(node)

OUT.write_text("\n".join(lines))
