"""Deep trace SpawnAttachments sequence in AutomaticBase."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_spawnatt_sequence.log")
lines = []

auto = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(auto))

spawn_ev = next(n for n in eg.list_all_nodes() if "SpawnAttachments" in str(n.get_node_title()) and n.get_class().get_name() == "K2Node_Event")

def walk(pin, depth=0, seen=None):
    if seen is None:
        seen = set()
    if not pin or depth > 40:
        return
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
        if lp.get_pin_direction() != unreal.EdGraphPinDirection.EGPD_INPUT:
            continue
        o = lp.get_owning_node()
        if id(o) in seen:
            continue
        seen.add(id(o))
        t = str(o.get_node_title()).replace("\n", " | ")
        pin_name = unreal.BlueprintGraphPinLibrary.get_pin_name(lp)
        lines.append(f"{'  '*depth}{o.get_name()} | {t} (via {pin_name})")
        if "SetStaticMesh" in t:
            for p in unreal.BlueprintEditorLibrary.list_all_pins(o):
                pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(p))
                if pn in ("self", "NewMesh"):
                    linked = [str(lp2.get_owning_node().get_node_title()) for lp2 in unreal.BlueprintGraphPinLibrary.list_connected_pins(p)]
                    val = unreal.BlueprintGraphPinLibrary.get_pin_value(p)
                    lines.append(f"{'  '*(depth+1)}{pn}={linked or val}")
        if o.get_class().get_name() == "K2Node_ExecutionSequence":
            for p in unreal.BlueprintEditorLibrary.list_all_pins(o):
                pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(p))
                if pn.startswith("then_") or pn == "then":
                    walk(p, depth + 1, seen)
        else:
            walk(o.find_output_pin("then"), depth + 1, seen)
            for branch in ("else",):
                walk(o.find_output_pin(branch), depth + 1, seen)

lines.append("=== From SpawnAttachments event ===")
walk(spawn_ev.find_output_pin("then"))

OUT.write_text("\n".join(lines))
