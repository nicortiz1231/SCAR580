"""Find all pins connected from Laser selection event."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_ui_laser_pins.log")
lines = []

wbp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Widgets/UI_WeaponModding.UI_WeaponModding")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(wbp))
node = next(n for n in eg.list_all_nodes() if "On Selection Changed (Laser)" in str(n.get_node_title()))

lines.append(f"{node.get_name()} | {node.get_node_title()}")
for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
    pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
    linked = []
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
        owner = lp.get_owning_node()
        linked.append(f"{owner.get_name()}:{str(unreal.BlueprintGraphPinLibrary.get_pin_name(lp))} | {owner.get_node_title()}")
    if linked:
        lines.append(f"  {pn} -> {linked}")

OUT.write_text("\n".join(lines))
