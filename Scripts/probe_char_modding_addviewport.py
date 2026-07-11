"""Find AddToViewport chain for UI_Modding on BP_FPCharacter."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_char_modding_addviewport.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(bp))

for node in eg.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    if "AddToViewport" in title or node.get_name() in ("K2Node_CallFunction_180", "K2Node_CreateWidget_2", "K2Node_VariableSet_23"):
        lines.append(f"\n{node.get_name()} | {title}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if pn in ("execute", "then", "self"):
                linked = [
                    f"{lp.get_owning_node().get_name()}:{str(unreal.BlueprintGraphPinLibrary.get_pin_name(lp))}"
                    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)
                ]
                lines.append(f"  {pn} -> {linked}")

OUT.write_text("\n".join(lines))
