"""Trace HOLOSIGHT / BP_Scope path in AutomaticBase."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_holosight_path.log")
lines = []

auto = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase")
for g in unreal.BlueprintEditorLibrary.list_graphs(auto):
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in ed.list_all_nodes():
        blob = f"{node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')}"
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            val = str(unreal.BlueprintGraphPinLibrary.get_pin_value(pin))
            if any(k in val for k in ("HOLOSIGHT", "NewEnumerator1", "BP_Scope", "4xScope", "ScopeSight")):
                blob += f" [{unreal.BlueprintGraphPinLibrary.get_pin_name(pin)}={val}]"
            if "BP_Scope" in val or "SM_4xScope" in val:
                lines.append(f"[{g.get_name()}] {blob}")
        if any(k in blob for k in ("BP_Scope", "ScopeRef", "HOLOSIGHT", "ENUM_Sights")):
            if node.get_class().get_name() == "K2Node_SwitchEnum":
                for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                    pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                    if pn.startswith("NewEnumerator"):
                        linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
                        lines.append(f"  {node.get_name()} {pn} -> {linked}")

OUT.write_text("\n".join(lines))
