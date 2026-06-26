"""List exec pins on sniper BeginPlay nodes."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_beginplay_pins.log")
lines = []

sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(sniper))

for name in ("K2Node_Event_0", "K2Node_CallParentFunction_0", "K2Node_CallFunction_0", "K2Node_CallFunction_1"):
    for node in eg.list_all_nodes():
        if node.get_name() != name:
            continue
        lines.append(f"=== {name} | {node.get_node_title()} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            d = unreal.BlueprintGraphPinLibrary.get_pin_direction(pin)
            cat = unreal.BlueprintGraphPinLibrary.get_pin_type(pin)
            linked = []
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                o = lp.get_owning_node()
                linked.append(f"{o.get_name()}:{unreal.BlueprintGraphPinLibrary.get_pin_name(lp)}")
            lines.append(f"  {pn} dir={d} cat={cat} links={linked}")

OUT.write_text("\n".join(lines))
