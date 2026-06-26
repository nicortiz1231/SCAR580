"""Check sniper parent class and AutomaticBase BeginPlay sight chain."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_automatic_base_beginplay.log")
lines = []

sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
lines.append(f"Sniper parent={sniper.parent_class.get_path_name() if sniper.parent_class else None}")

auto = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(auto))

# find BeginPlay parent call
begin = None
for node in eg.list_all_nodes():
    if node.get_class().get_name() == "K2Node_CallParentFunction" and "BeginPlay" in str(node.get_node_title()):
        begin = node
        break

lines.append("=== AutomaticBase BeginPlay chain ===")
if begin:
    then = begin.find_output_pin("then")
    stack = [then]
    depth = 0
    while stack and depth < 35:
        pin = stack.pop()
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            if lp.get_pin_direction() != unreal.EdGraphPinDirection.EGPD_INPUT:
                continue
            o = lp.get_owning_node()
            t = str(o.get_node_title()).replace("\n", " | ")
            lines.append(f"{'  '*min(depth,8)}{o.get_name()} | {t}")
            if o.get_class().get_name() == "K2Node_SwitchEnum" and "Sights" in t:
                for p in unreal.BlueprintEditorLibrary.list_all_pins(o):
                    pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(p))
                    if pn.startswith("NewEnumerator"):
                        for lp2 in unreal.BlueprintGraphPinLibrary.list_connected_pins(p):
                            o2 = lp2.get_owning_node()
                            lines.append(f"{'  '*(min(depth,8)+1)}[{pn}] {o2.get_name()} | {str(o2.get_node_title()).replace(chr(10),' | ')[:80]}")
            nxt = o.find_output_pin("then")
            if nxt:
                stack.append(nxt)
            depth += 1

# SpawnAttachments on automatic base?
for g in unreal.BlueprintEditorLibrary.list_graphs(auto):
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in ed.list_all_nodes():
        if "SpawnAttachments" in str(node.get_node_title()):
            lines.append(f"[{g.get_name()}] {node.get_name()} | {node.get_node_title()}")

OUT.write_text("\n".join(lines))
