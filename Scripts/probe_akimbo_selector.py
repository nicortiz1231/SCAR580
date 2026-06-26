"""Dump AkimboSelector and sniper EventGraph BeginPlay chain."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_akimbo_selector.log")
lines = []

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    gname = g.get_name()
    if "Akimbo" not in gname and gname != "EventGraph":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append(f"=== {gname} ===")
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        lines.append(f"{node.get_name()} | {title}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if pn in ("execute", "then", "NewMesh", "Selection", "Sight", "Condition"):
                linked = [f"{lp.get_owning_node().get_name()}" for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
                val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                if linked or val:
                    lines.append(f"  {pn} -> {linked or val}")

sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(sniper))
lines.append("=== Sniper EventGraph ===")
for node in eg.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    lines.append(f"{node.get_name()} | {title}")

OUT.write_text("\n".join(lines))
