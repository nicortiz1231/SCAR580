"""List every item graph + search AimDownSight + parent pickup class."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_item_all_graphs_full.log")
lines = []

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append(f"GRAPH {g.get_name()} ({len(ed.list_all_nodes())} nodes)")

for gname in ("AimDownSight", "AkimboSelector"):
    g = next((g for g in unreal.BlueprintEditorLibrary.list_graphs(item) if g.get_name() == gname), None)
    if not g:
        lines.append(f"MISSING {gname}")
        continue
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append(f"=== {gname} ===")
    for node in ed.list_all_nodes():
        t = str(node.get_node_title()).replace("\n", " | ")
        lines.append(f"  {node.get_name()} | {t}")
        if "SetStaticMesh" in t:
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                if pn in ("NewMesh", "self"):
                    linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
                    val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                    lines.append(f"    {pn} -> {linked or val}")

pickup = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Pickup_Sniper.BP_Weapon_Pickup_Sniper")
try:
    parent = pickup.get_editor_property("parent_class")
    lines.append(f"pickup parent={parent}")
except Exception as e:
    lines.append(f"pickup parent ERR {e}")

# sniper current state
sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(sniper))
lines.append(f"SCAR sniper EventGraph {len(eg.list_all_nodes())} nodes")
for node in eg.list_all_nodes():
    lines.append(f"  {node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')}")

cdo = unreal.get_default_object(sniper.generated_class())
lines.append(f"AimDistance={cdo.get_editor_property('AimDistanceFromCamera')}")

OUT.write_text("\n".join(lines))
