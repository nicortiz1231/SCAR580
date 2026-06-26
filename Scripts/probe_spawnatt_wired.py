import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_spawnatt_wired.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(bp)
)

for name in ("K2Node_CallFunction_212", "K2Node_CallFunction_234"):
    for node in editor.list_all_nodes():
        if node.get_name() != name:
            continue
        lines.append(f"=== {name} ===")
        then = node.find_then_pin()
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
            o = lp.get_owning_node()
            lines.append(f"  then -> {o.get_name()} | {str(o.get_node_title()).replace(chr(10),' | ')}")

# sniper beginplay nodes
sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
editor2 = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(sniper)
)
lines.append("=== sniper EventGraph ===")
for node in editor2.list_all_nodes():
    lines.append(f"  {node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')}")

OUT.write_text("\n".join(lines))
