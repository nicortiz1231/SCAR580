"""Trace SetAmmo and SpawnAttachments in BP_Item_Base."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_setammo_spawnatt.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")

for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                owner = lp.get_owning_node()
                if owner.get_name() == "K2Node_CustomEvent_3" or "SpawnAttachments" in str(owner.get_node_title()):
                    pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                    lines.append(
                        f"SpawnAtt IN from [{g.get_name()}] {node.get_name()} "
                        f"{str(node.get_node_title()).replace(chr(10),' | ')} pin={pname}"
                    )

# SetAmmo function body
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if g.get_name() != "SetAmmo":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append("=== SetAmmo graph ===")
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        lines.append(f"  {node.get_name()} | {title}")

# AimDownSight graph
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if "Aim" not in g.get_name():
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append(f"=== {g.get_name()} ===")
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        lines.append(f"  {node.get_name()} | {title}")
        if node.get_class().get_name() == "K2Node_VariableGet":
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) == unreal.EdGraphPinDirection.EGPD_OUTPUT:
                    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                        owner = lp.get_owning_node()
                        lines.append(f"    -> {owner.get_name()} | {str(owner.get_node_title()).replace(chr(10),' | ')}")

OUT.write_text("\n".join(lines))
