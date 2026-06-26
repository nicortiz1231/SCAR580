"""Find SetWeaponAmmoData calls on character and spawn chain."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_char_setweaponammo.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(bp))

for node in editor.list_all_nodes():
    t = str(node.get_node_title()).replace("\n", " | ")
    if "SetWeaponAmmoData" in t:
        lines.append(f"{node.get_name()} | {t}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if pn in ("execute", "then", "self"):
                linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
                if linked:
                    lines.append(f"  {pn} -> {linked}")

# spawn chain
for name in ("K2Node_VariableSet_19", "K2Node_CallFunction_496", "K2Node_CallFunction_234", "K2Node_BreakStruct_9", "K2Node_VariableGet_65"):
    for node in editor.list_all_nodes():
        if node.get_name() != name:
            continue
        lines.append(f"=== {name} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            if linked or val:
                lines.append(f"  {pn} -> {linked or val}")

OUT.write_text("\n".join(lines))
