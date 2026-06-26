"""Probe SetAmmo calls on swap and item data copy."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_setammo_swap.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(bp)
)

for name in ("K2Node_CallFunction_234", "K2Node_CallFunction_212", "K2Node_VariableGet_77", "K2Node_BreakStruct_1"):
    for node in editor.list_all_nodes():
        if node.get_name() != name:
            continue
        lines.append(f"=== {name} | {str(node.get_node_title()).replace(chr(10),' | ')} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            linked = []
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                owner = lp.get_owning_node()
                linked.append(f"{owner.get_name()}:{pname}")
            try:
                val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                if val:
                    linked.append(f"val={val!r}")
            except Exception:
                pass
            lines.append(f"  {pname} -> {linked}")

# Search Set ItemData on character graph
for node in editor.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    if "Set ItemData" in title:
        lines.append(f"SET_ITEMDATA {node.get_name()} | {title}")

OUT.write_text("\n".join(lines))
