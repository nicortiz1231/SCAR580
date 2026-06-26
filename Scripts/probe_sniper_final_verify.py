"""Verify sniper spawn path has SetWeaponAmmoData and BeginPlay scope chain."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sniper_final_verify.log")
lines = []

char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
ced = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))
for name in ("K2Node_VariableSet_15", "K2Node_CallFunction_212", "K2Node_CallFunction_141"):
    for node in ced.list_all_nodes():
        if node.get_name() != name:
            continue
        lines.append(f"=== {name} | {node.get_node_title()} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if pn in ("execute", "then", "self"):
                linked = [f"{lp.get_owning_node().get_name()}:{unreal.BlueprintGraphPinLibrary.get_pin_name(lp)}" for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
                if linked:
                    lines.append(f"  {pn} -> {linked}")

for node in ced.list_all_nodes():
    if "SetWeaponAmmoData" not in str(node.get_node_title()):
        continue
    exec_in = node.find_input_pin("execute")
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(exec_in):
        if lp.get_owning_node().get_name() == "K2Node_VariableSet_15":
            lines.append(f"FOUND SetWeaponAmmoData fed from Set SpawnedItem_15: {node.get_name()}")

sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(sniper))
lines.append("\n=== Sniper BeginPlay chain ===")
for name in ("K2Node_Event_0", "K2Node_CallParentFunction_0", "K2Node_CallFunction_0", "K2Node_CallFunction_1"):
    for node in eg.list_all_nodes():
        if node.get_name() != name:
            continue
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if pn in ("execute", "then"):
                linked = [f"{lp.get_owning_node().get_name()}:{unreal.BlueprintGraphPinLibrary.get_pin_name(lp)}" for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
                if linked:
                    lines.append(f"  {name}.{pn} -> {linked}")

cdo = unreal.get_default_object(sniper.generated_class())
lines.append(f"\nCDO AimDistance={cdo.get_editor_property('AimDistanceFromCamera')} Scope={cdo.get_editor_property('ScopeSightMesh').get_name()} Optic={cdo.get_editor_property('OpticSightMesh').get_name()}")

OUT.write_text("\n".join(lines))
