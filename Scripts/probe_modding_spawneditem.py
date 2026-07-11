"""Trace modding path from SpawnedItem VariableGet_130 and fix candidates."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_modding_spawneditem.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(bp))

for name in (
    "K2Node_VariableGet_106", "K2Node_VariableGet_130", "K2Node_VariableGet_144",
    "K2Node_IfThenElse_27", "K2Node_CreateWidget_2", "K2Node_CallFunction_201",
    "K2Node_CallFunction_180", "K2Node_CallFunction_188", "K2Node_CallFunction_134",
):
    node = next((n for n in eg.list_all_nodes() if n.get_name() == name), None)
    if not node:
        lines.append(f"MISSING {name}")
        continue
    lines.append(f"\n=== {name} | {node.get_node_title()} ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        d = unreal.BlueprintGraphPinLibrary.get_pin_direction(pin)
        dir_s = "IN" if d == unreal.EdGraphPinDirection.EGPD_INPUT else "OUT"
        linked = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            owner = lp.get_owning_node()
            linked.append(f"{owner.get_name()}:{str(unreal.BlueprintGraphPinLibrary.get_pin_name(lp))}")
        if linked or pn in ("execute", "then", "else", "Condition", "SpawnedItem", "UI_Modding", "ReturnValue"):
            lines.append(f"  {dir_s} {pn} -> {linked}")

# search any exec fed into VariableGet_144
lines.append("\n=== exec inputs to VariableGet_144 ===")
vg144 = next(n for n in eg.list_all_nodes() if n.get_name() == "K2Node_VariableGet_144")
exec_in = vg144.find_input_pin("execute")
for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(exec_in):
    lines.append(f"  from {lp.get_owning_node().get_name()}")

# all nodes connecting TO VariableGet_144 execute
for node in eg.list_all_nodes():
    then = node.find_output_pin("then")
    if not then:
        continue
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
        if lp.get_owning_node().get_name() == "K2Node_VariableGet_144":
            lines.append(f"  exec from {node.get_name()} | {node.get_node_title()}")

OUT.write_text("\n".join(lines))
