"""Find reusable PlayerController / Self nodes on BP_FPCharacter."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_char_pc_nodes.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(bp))

for node in eg.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    if "GetPlayerController" in title or node.get_class().get_name() == "K2Node_Self":
        lines.append(f"{node.get_name()} | {title}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if pn in ("ReturnValue", "self", "WorldContextObject"):
                linked = [f"{lp.get_owning_node().get_name()}:{str(unreal.BlueprintGraphPinLibrary.get_pin_name(lp))}" for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
                lines.append(f"  {pn} -> {linked}")

OUT.write_text("\n".join(lines))
