"""Trace SetWeaponAmmoData exec flow after Set ItemData."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_setweaponammo_flow.log")
lines = []

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    if g.get_name() != "SetWeaponAmmoData":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        if node.get_name() != "K2Node_VariableSet_7":
            continue
        lines.append("=== after Set ItemData ===")
        then = node.find_output_pin("then")
        stack = [(then, 0)]
        while stack:
            pin, depth = stack.pop()
            if not pin or depth > 25:
                continue
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                if lp.get_pin_direction() != unreal.EdGraphPinDirection.EGPD_INPUT:
                    continue
                o = lp.get_owning_node()
                lines.append(f"{'  '*depth}{o.get_name()} | {str(o.get_node_title()).replace(chr(10),' | ')}")
                nxt = o.find_output_pin("then")
                if nxt:
                    stack.append((nxt, depth + 1))

# all graphs with OpticSight SetStaticMesh in item
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        title = str(node.get_node_title())
        if "SetStaticMesh" not in title:
            continue
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            if str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin)) != "self":
                continue
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                o = lp.get_owning_node()
                if "OpticSight" in str(o.get_node_title()):
                    lines.append(f"OPTIC SET [{g.get_name()}] {node.get_name()}")

OUT.write_text("\n".join(lines))
