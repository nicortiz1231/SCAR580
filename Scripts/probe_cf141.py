import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_cf141.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(bp)
)
for node in editor.list_all_nodes():
    if node.get_name() != "K2Node_CallFunction_141":
        continue
    lines.append(str(node.get_node_title()).replace("\n", " | "))
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        if pn not in ("execute", "then", "self"):
            continue
        linked = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            o = lp.get_owning_node()
            linked.append(o.get_name())
        lines.append(f"  {pn} -> {linked}")

OUT.write_text("\n".join(lines))
