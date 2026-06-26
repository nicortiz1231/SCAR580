import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_char_set_itemdata.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(bp)
)
for node in editor.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    if "ItemData" not in title and "SetWeaponAmmoData" not in title:
        continue
    if node.get_class().get_name() not in ("K2Node_VariableSet", "K2Node_CallFunction"):
        continue
    lines.append(f"{node.get_name()} | {title}")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        if pn in ("execute", "then", "self", "ItemData"):
            linked = []
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                o = lp.get_owning_node()
                linked.append(o.get_name())
            if linked:
                lines.append(f"  {pn} -> {linked}")

OUT.write_text("\n".join(lines))
