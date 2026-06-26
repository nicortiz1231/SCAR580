"""What triggers sight mesh apply in AutomaticBase?"""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sight_trigger.log")
lines = []

auto = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase")

for g in unreal.BlueprintEditorLibrary.list_graphs(auto):
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in ed.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        cls = node.get_class().get_name()
        if cls in ("K2Node_Event", "K2Node_CustomEvent", "K2Node_CallParentFunction"):
            if any(k in title for k in ("BeginPlay", "SpawnAttachment", "Construction", "Parent")):
                lines.append(f"[{g.get_name()}] {node.get_name()} | {title}")
        if "Switch on ENUM_Sights" in title:
            lines.append(f"[{g.get_name()}] SIGHT_SWITCH {node.get_name()}")
            exec_in = node.find_input_pin("execute")
            if exec_in:
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(exec_in):
                    src = lp.get_owning_node()
                    lines.append(f"  exec from {src.get_name()} | {str(src.get_node_title()).replace(chr(10),' | ')}")

# SpawnAttachments on item base - any implementation in functions?
item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    if "SpawnAttachment" not in g.get_name():
        continue
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append(f"\n=== Item graph {g.get_name()} ({len(ed.list_all_nodes())} nodes) ===")
    for node in ed.list_all_nodes():
        lines.append(f"  {node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')}")

OUT.write_text("\n".join(lines))
