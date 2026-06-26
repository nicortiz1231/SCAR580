"""Trace item base BeginPlay and attachment sight application."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_item_beginplay.log")
lines = []

ITEM = "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base"
item = unreal.load_asset(ITEM)


def walk_exec(node, depth=0, seen=None):
    if seen is None:
        seen = set()
    if depth > 20 or id(node) in seen:
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
        walk_exec(lp.get_owning_node(), depth + 1, seen)


for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    begin = editor.find_event_node("ReceiveBeginPlay") if g.get_name() == "EventGraph" else None
    if begin:
        lines.append("=== Item BeginPlay chain ===")
        walk_exec(begin)

    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if "Switch on ENUM_Sights" in title or "Break ST Attachments" in title:
            lines.append(f"[{g.get_name()}] {node.get_name()} | {title}")

# sniper parent beginplay
sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
seg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(sniper))
lines.append("=== Sniper BeginPlay full ===")
walk_exec(seg.find_event_node("ReceiveBeginPlay"))

OUT.write_text("\n".join(lines))
