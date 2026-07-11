"""Trace IfThenElse_0 + SpawnAttachments chain in UI_WeaponModding."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_modding_selection_chain.log")
lines = []

wbp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Widgets/UI_WeaponModding.UI_WeaponModding")
eg = unreal.BlueprintEditorLibrary.find_event_graph(wbp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)

TARGETS = {
    "K2Node_IfThenElse_0",
    "K2Node_IfThenElse_1",
    "K2Node_VariableGet_4",
    "K2Node_CallFunction_24",
    "K2Node_CallFunction_36",
    "K2Node_ComponentBoundEvent_0",
}

for node in editor.list_all_nodes():
    if node.get_name() not in TARGETS:
        continue
    lines.append(f"\n=== {node.get_name()} | {node.get_node_title()} ===")
    for pin in node.get_pins():
        if not pin.is_connected():
            continue
        for link in pin.get_linked_pins():
            owner = link.get_owning_node()
            lines.append(
                f"  {pin.get_name()} -> {owner.get_name()} | {owner.get_node_title()} :: {link.get_name()}"
            )

# Walk from Laser selection event
for node in editor.list_all_nodes():
    if "On Selection Changed (Laser)" not in str(node.get_node_title()):
        continue
    lines.append(f"\n=== Laser selection start: {node.get_name()} ===")
    then = node.find_output_pin("then")
    if then:
        for link in then.list_connected_pins():
            owner = link.get_owning_node()
            lines.append(f"  then -> {owner.get_name()} | {owner.get_node_title()}")

OUT.write_text("\n".join(lines))
unreal.log(f"[probe_modding_selection_chain] wrote {OUT}")
