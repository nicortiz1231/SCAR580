"""Trace pickup equip vs wheel sniper spawn on original Bodycam character."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_pickup_vs_wheel.log")
lines = []

char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
ed = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))

def dump_node(name):
    for node in ed.list_all_nodes():
        if node.get_name() != name:
            continue
        lines.append(f"=== {name} | {str(node.get_node_title()).replace(chr(10),' | ')} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            linked = [f"{lp.get_owning_node().get_name()}:{unreal.BlueprintGraphPinLibrary.get_pin_name(lp)}" for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            if linked or val:
                lines.append(f"  {pn} -> {linked or val}")

# pickup overlap equip path
for name in ("K2Node_CallFunction_46", "K2Node_CallFunction_17", "K2Node_CallFunction_18", "K2Node_CallFunction_20"):
    dump_node(name)

# wheel sniper spawn
for name in ("K2Node_SpawnActorFromClass_1", "K2Node_VariableSet_15", "K2Node_CallFunction_157", "K2Node_CallFunction_212", "K2Node_CallFunction_141", "K2Node_CallFunction_140"):
    dump_node(name)

# any SetWeaponAmmoData on character
lines.append("\n=== All SetWeaponAmmoData calls on character ===")
for node in ed.list_all_nodes():
    if "SetWeaponAmmoData" not in str(node.get_node_title()):
        continue
    lines.append(f"  {node.get_name()} | exec_in={[lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(node.find_input_pin('execute'))] if node.find_input_pin('execute') else []}")
    is_pickup = node.find_input_pin("IsPickUp")
    if is_pickup:
        lines.append(f"    IsPickUp={unreal.BlueprintGraphPinLibrary.get_pin_value(is_pickup)}")

OUT.write_text("\n".join(lines))
