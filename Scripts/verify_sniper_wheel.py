"""Verify sniper wheel wiring on BP_FPCharacter."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/verify_sniper_wheel.log")
lines = []

SNIPER = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper_C"
EMPTY = "/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_EmptyHands.BP_Weapon_EmptyHands_C"

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)

for node in editor.list_all_nodes():
    if node.get_name() == "K2Node_SpawnActorFromClass_1":
        pin = node.find_input_pin("Class")
        lines.append(f"fallback_spawn={unreal.BlueprintGraphPinLibrary.get_pin_value(pin)!r}")

for node in editor.list_all_nodes():
    if node.get_name() == "K2Node_MacroInstance_7":
        exec_pin = node.find_input_pin("execute")
        linked = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(exec_pin):
            owner = lp.get_owning_node()
            linked.append(owner.get_name())
        lines.append(f"begin_setup_exec_from={linked}")

for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if g.get_name() != "BeginSetup":
        continue
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in ed.list_all_nodes():
        if node.get_name() != "K2Node_GenericCreateObject_2":
            continue
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if pname.startswith("ItemData_WeaponData"):
                lines.append(
                    f"hands_construct={unreal.BlueprintGraphPinLibrary.get_pin_value(pin)!r}"
                )

lines.append(f"expect_sniper={SNIPER!r}")
lines.append(f"empty_hands={EMPTY!r}")
OUT.write_text("\n".join(lines))
