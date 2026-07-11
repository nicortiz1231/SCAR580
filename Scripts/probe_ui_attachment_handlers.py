"""Trace knot after laser selection and compare sight handler."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_ui_attachment_handlers.log")
lines = []

wbp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Widgets/UI_WeaponModding.UI_WeaponModding")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(wbp))

for label in ("Laser", "Sight", "Muzzle", "GRIP"):
    node = next((n for n in eg.list_all_nodes() if f"On Selection Changed ({label})" in str(n.get_node_title())), None)
    if not node:
        continue
    lines.append(f"\n=== {label} ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            owner = lp.get_owning_node()
            lines.append(f"  {pn} -> {owner.get_name()} | {owner.get_node_title()}")
            # follow knot output
            if owner.get_class().get_name() == "K2Node_Knot":
                out = owner.find_output_pin("OutputPin")
                if out:
                    for lp2 in unreal.BlueprintGraphPinLibrary.list_connected_pins(out):
                        o2 = lp2.get_owning_node()
                        lines.append(f"    knot -> {o2.get_name()} | {o2.get_node_title()}")

OUT.write_text("\n".join(lines))
