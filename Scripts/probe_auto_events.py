"""Trace AutomaticBase ParentBeginPlay and SpawnAttachments events."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_auto_events.log")
lines = []

auto = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(auto))

def trace_from(event_name, max_depth=30):
    ev = None
    for node in eg.list_all_nodes():
        if event_name in str(node.get_node_title()) and node.get_class().get_name() == "K2Node_Event":
            ev = node
            break
    if not ev:
        lines.append(f"MISSING {event_name}")
        return
    lines.append(f"=== {event_name} ===")
    then = ev.find_output_pin("then")
    stack = [(then, 0)]
    while stack:
        pin, depth = stack.pop()
        if not pin or depth > max_depth:
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            if lp.get_pin_direction() != unreal.EdGraphPinDirection.EGPD_INPUT:
                continue
            o = lp.get_owning_node()
            t = str(o.get_node_title()).replace("\n", " | ")
            lines.append(f"{'  '*depth}{o.get_name()} | {t}")
            if "Switch on ENUM_Sights" in t:
                sel = o.find_input_pin("Selection")
                if sel:
                    for lp2 in unreal.BlueprintGraphPinLibrary.list_connected_pins(sel):
                        lines.append(f"{'  '*(depth+1)}Selection<-{lp2.get_owning_node().get_name()} | {lp2.get_owning_node().get_node_title()}")
            for branch in ("then", "else"):
                nxt = o.find_output_pin(branch)
                if nxt:
                    stack.append((nxt, depth + 1))

trace_from("ParentBeginPlay")
trace_from("SpawnAttachments")

OUT.write_text("\n".join(lines))
