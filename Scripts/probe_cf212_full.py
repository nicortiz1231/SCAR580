import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_cf212_full.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(bp)
)
for node in editor.list_all_nodes():
    if node.get_name() not in ("K2Node_CallFunction_212", "K2Node_CallFunction_140", "K2Node_CallFunction_234"):
        continue
    lines.append(f"=== {node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')} ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        linked = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            o = lp.get_owning_node()
            linked.append(o.get_name())
        if linked or pn in ("execute", "then", "self"):
            lines.append(f"  {pn} -> {linked}")

OUT.write_text("\n".join(lines))
