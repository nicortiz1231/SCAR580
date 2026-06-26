"""Find sniper spawn and pickup equip paths in Bodycam character."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_char_sniper_paths.log")
lines = []

char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
ed = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))

lines.append("=== SpawnActor nodes ===")
for node in ed.list_all_nodes():
    if node.get_class().get_name() != "K2Node_SpawnActorFromClass":
        continue
    cls_pin = node.find_input_pin("Class")
    val = unreal.BlueprintGraphPinLibrary.get_pin_value(cls_pin) if cls_pin else ""
    lines.append(f"  {node.get_name()} Class={val}")

lines.append("\n=== Nodes referencing Sniper ===")
for node in ed.list_all_nodes():
    blob = node.get_name()
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        val = str(unreal.BlueprintGraphPinLibrary.get_pin_value(pin))
        if "Sniper" in val:
            blob += f" [{unreal.BlueprintGraphPinLibrary.get_pin_name(pin)}={val}]"
    if "Sniper" in blob:
        lines.append(f"  {blob} | {str(node.get_node_title()).replace(chr(10),' ')}")

# HandsSlot - all construct nodes with weapon data
lines.append("\n=== BeginSetup weapon ItemData ===")
for g in unreal.BlueprintEditorLibrary.list_graphs(char):
    if g.get_name() != "BeginSetup":
        continue
    ged = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in ged.list_all_nodes():
        if node.get_class().get_name() != "K2Node_GenericCreateObject":
            continue
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            val = str(unreal.BlueprintGraphPinLibrary.get_pin_value(pin))
            if val and ("Sniper" in val or "WeaponData" in str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))):
                lines.append(f"  {node.get_name()} {unreal.BlueprintGraphPinLibrary.get_pin_name(pin)}={val}")

# SwapWeapon / wheel
for g in unreal.BlueprintEditorLibrary.list_graphs(char):
    if "Swap" not in g.get_name() and "Weapon" not in g.get_name():
        continue
    ged = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in ged.list_all_nodes():
        title = str(node.get_node_title())
        if "Sniper" in title or (node.get_class().get_name() == "K2Node_SpawnActorFromClass"):
            lines.append(f"[{g.get_name()}] {node.get_name()} | {title.replace(chr(10),' ')}")

OUT.write_text("\n".join(lines))
