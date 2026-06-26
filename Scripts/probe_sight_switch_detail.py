"""What connects to ENUM_Sights switch Selection and NewEnumerator1 branch."""
import unreal
from pathlib import Path

auto = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(auto))
sw = next(n for n in eg.list_all_nodes() if n.get_name() == "K2Node_SwitchEnum_1")
lines = []
lines.append("=== Selection input ===")
sel = sw.find_input_pin("Selection")
for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(sel):
    o = lp.get_owning_node()
    lines.append(f"  {o.get_name()} | {o.get_node_title()}")
    for p in unreal.BlueprintEditorLibrary.list_all_pins(o):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(p))
        if "Sight" in pn or "Attachment" in pn:
            for lp2 in unreal.BlueprintGraphPinLibrary.list_connected_pins(p):
                lines.append(f"    {pn} <- {lp2.get_owning_node().get_name()}")

for pin in unreal.BlueprintEditorLibrary.list_all_pins(sw):
    pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
    if not pn.startswith("NewEnumerator"):
        continue
    linked = []
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
        o = lp.get_owning_node()
        linked.append(f"{o.get_name()}|{str(o.get_node_title()).replace(chr(10),' ')[:70]}")
    lines.append(f"{pn} -> {linked or 'OPEN'}")

Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sight_switch_detail.log").write_text("\n".join(lines))
