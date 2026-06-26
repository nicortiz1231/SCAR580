"""Character ADS FOV switches: which sight enums wired."""
import unreal
from pathlib import Path

lines = []
bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
ed = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(bp))
for sw_name in ("K2Node_SwitchEnum_3", "K2Node_SwitchEnum_4"):
    for node in ed.list_all_nodes():
        if node.get_name() != sw_name:
            continue
        lines.append(f"=== {sw_name} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if pn not in ("NewEnumerator1", "NewEnumerator2", "NewEnumerator7", "Selection"):
                continue
            if pn == "Selection":
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                    lines.append(f"  Selection <- {lp.get_owning_node().get_name()} | {lp.get_owning_node().get_node_title()}")
                continue
            linked = [str(lp.get_owning_node().get_node_title()).replace("\n"," ")[:50] for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
            lines.append(f"  {pn} -> {linked or 'OPEN'}")

Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_char_ads_sight.log").write_text("\n".join(lines))
