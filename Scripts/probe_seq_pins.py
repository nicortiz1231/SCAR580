import unreal
from pathlib import Path

auto = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(auto))
seq = next(n for n in eg.list_all_nodes() if n.get_name() == "K2Node_ExecutionSequence_6")
lines = []
for pin in unreal.BlueprintEditorLibrary.list_all_pins(seq):
    pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
    if not pn.startswith("then"):
        continue
    linked = [f"{lp.get_owning_node().get_name()}|{lp.get_owning_node().get_node_title()}" for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
    lines.append(f"{pn} -> {linked}")
Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_seq_pins.log").write_text("\n".join(lines))
