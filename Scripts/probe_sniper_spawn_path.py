"""Trace sniper spawn path: SwitchEnum sights, SpawnAttachments, SetWeaponAmmoData."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sniper_spawn_path.log")
lines = []

char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))

TARGETS = {
    "K2Node_SpawnActorFromClass_1",
    "K2Node_VariableSet_15",
    "K2Node_CallFunction_212",
    "K2Node_CallFunction_141",
    "K2Node_VariableGet_83",
    "K2Node_SwitchEnum_3",
    "K2Node_SwitchEnum_4",
    "K2Node_BreakStruct_11",
    "K2Node_BreakStruct_9",
    "K2Node_VariableGet_65",
}

for node in editor.list_all_nodes():
    name = node.get_name()
    if name not in TARGETS and "Sniper" not in str(node.get_node_title()):
        continue
    title = str(node.get_node_title()).replace("\n", " | ")
    lines.append(f"=== {name} | {title} ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        linked = [f"{lp.get_owning_node().get_name()}:{unreal.BlueprintGraphPinLibrary.get_pin_name(lp)}" for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
        val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
        if linked or (val and pn not in ("execute", "then")):
            lines.append(f"  {pn} -> {linked or val}")

# pickup PrimaryEquip SetWeaponAmmoData wiring
pickup = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Pickup.BP_Item_Pickup")
ped = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(pickup))
lines.append("\n=== PICKUP PrimaryEquip SetWeaponAmmoData ===")
for node in ped.list_all_nodes():
    if "SetWeaponAmmoData" not in str(node.get_node_title()):
        continue
    lines.append(f"{node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')}")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        linked = [f"{lp.get_owning_node().get_name()}:{unreal.BlueprintGraphPinLibrary.get_pin_name(lp)}" for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
        val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
        if linked or val:
            lines.append(f"  {pn} -> {linked or val}")

# item SpawnAttachments graph
item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    if "SpawnAttachment" not in g.get_name() and g.get_name() != "EventGraph":
        continue
    ged = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in ged.list_all_nodes():
        title = str(node.get_node_title())
        if "SpawnAttachment" not in title and "SetStaticMesh" not in title and "OpticSight" not in title and "ScopeSight" not in title:
            continue
        lines.append(f"\n[{g.get_name()}] {node.get_name()} | {title.replace(chr(10),' | ')}")
        then = node.find_output_pin("then")
        if then:
            linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then)]
            if linked:
                lines.append(f"  then -> {linked}")

OUT.write_text("\n".join(lines))
