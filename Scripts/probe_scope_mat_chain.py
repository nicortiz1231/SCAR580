"""Trace scope material SetScalar calls and FOV branch logic."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_scope_mat_chain.log")
lines = []

char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))

TARGETS = (
    "K2Node_CallFunction_128", "K2Node_CallFunction_144",
    "K2Node_CallFunction_193", "K2Node_CallFunction_60", "K2Node_CallFunction_44",
    "K2Node_IfThenElse_17", "K2Node_SwitchEnum_3", "K2Node_SwitchEnum_4",
    "K2Node_VariableGet_142", "K2Node_VariableGet_151", "K2Node_VariableGet_52",
)

for name in TARGETS:
    for node in eg.list_all_nodes():
        if node.get_name() != name:
            continue
        title = str(node.get_node_title()).replace("\n", " | ")
        lines.append(f"\n=== {name} | {title} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            linked = []
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                o = lp.get_owning_node()
                linked.append(f"{o.get_name()}|{str(o.get_node_title()).replace(chr(10),' ')[:35]}")
            if val or linked or pn in ("execute", "then", "Condition", "TargetFOV"):
                lines.append(f"  {pn} val={val!r} linked={linked}")

# Find all SetScalarParameterValue nodes
lines.append("\n=== SetScalarParameter nodes ===")
for node in eg.list_all_nodes():
    title = str(node.get_node_title())
    if "ScalarParameter" not in title and "SetScalar" not in title:
        continue
    lines.append(f"  {node.get_name()} | {title.replace(chr(10),' | ')}")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
        if val:
            lines.append(f"    {pn}={val}")

OUT.write_text("\n".join(lines))
