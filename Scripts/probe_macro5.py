"""Trace Material Reload macro 5 completion and BP_Scope spawn for enum7."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_macro5.log")
lines = []

auto = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase"
)
ed = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(auto)
)

for name in ("K2Node_MacroInstance_5", "K2Node_CallFunction_6", "K2Node_CallFunction_78", "K2Node_CallFunction_79"):
    for node in ed.list_all_nodes():
        if node.get_name() != name:
            continue
        lines.append(f"\n=== {name} | {str(node.get_node_title()).replace(chr(10),' | ')} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            if linked or val:
                lines.append(f"  {pn} val={val!r} linked={linked}")

# VariableGet_144 ScopeMesh source
for node in ed.list_all_nodes():
    if node.get_name() != "K2Node_VariableGet_144":
        continue
    lines.append(f"\n=== VariableGet_144 ===")
    lines.append(f"  title={str(node.get_node_title()).replace(chr(10),' | ')}")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
        linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
        if val or linked:
            lines.append(f"  {pn} val={val!r} linked={linked}")

OUT.write_text("\n".join(lines))
