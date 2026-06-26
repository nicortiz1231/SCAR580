"""Dump every ENUM_Sights branch target in AutomaticBase."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sights_enum_all.log")
lines = []

auto = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(auto))

for node in eg.list_all_nodes():
    if "ENUM_Sights" not in str(node.get_node_title()):
        continue
    lines.append(f"=== {node.get_name()} ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        if not pn.startswith("NewEnumerator"):
            continue
        targets = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            o = lp.get_owning_node()
            targets.append(str(o.get_node_title()).replace("\n", " "))
        lines.append(f"  {pn}: {targets or 'OPEN'}")

Path(OUT).write_text("\n".join(lines))
