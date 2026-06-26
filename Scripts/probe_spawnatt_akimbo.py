"""Dump item SpawnAttachments event exec chain and Akimbo Spawner sight logic."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_spawnatt_akimbo.log")
lines = []

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")


def walk_from(node, depth=0, seen=None):
    if seen is None:
        seen = set()
    if depth > 40 or id(node) in seen:
        return
    seen.add(id(node))
    title = str(node.get_node_title()).replace("\n", " | ")
    lines.append(f"{'  '*depth}{node.get_name()} | {title}")
    then = node.find_output_pin("then")
    if then:
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
            if lp.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT:
                walk_from(lp.get_owning_node(), depth + 1, seen)
    if node.get_class().get_name() == "K2Node_IfThenElse":
        for pin_name in ("else",):
            pin = node.find_output_pin(pin_name)
            if pin:
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                    if lp.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT:
                        lines.append(f"{'  '*(depth+1)}[else]-> {lp.get_owning_node().get_name()}")


for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        if node.get_class().get_name() != "K2Node_CustomEvent":
            continue
        if "SpawnAttachments" not in str(node.get_node_title()):
            continue
        lines.append(f"=== SpawnAttachments in {g.get_name()} ===")
        walk_from(node)

# Akimbo Spawner graph - sight mesh selection
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    if g.get_name() != "Akimbo Spawner":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append("=== Akimbo Spawner sight-related nodes ===")
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if any(k in title for k in ("Sight", "Scope", "Optic", "SetStaticMesh", "ENUM_Sights", "Switch")):
            lines.append(f"  {node.get_name()} | {title}")
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                if pn in ("NewMesh", "Selection", "Condition", "self"):
                    linked = []
                    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                        linked.append(lp.get_owning_node().get_name())
                    val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                    if linked or val:
                        lines.append(f"    {pn} -> {linked or val}")

OUT.write_text("\n".join(lines))
