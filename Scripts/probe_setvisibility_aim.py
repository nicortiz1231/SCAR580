"""Trace SetVisibility nodes tied to IsAim/Reload on AutomaticBase."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_setvisibility_aim.log")
lines = []

bp = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase"
)
graph = None
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if g.get_name() == "EventGraph":
        graph = g
        break

ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
target_ids = {
    "K2Node_CallFunction_95",
    "K2Node_CallFunction_96",
    "K2Node_CallFunction_97",
    "K2Node_CallFunction_116",
    "K2Node_CallFunction_124",
}

for node in ed.list_all_nodes():
    if node.get_name() not in target_ids:
        continue
    lines.append(f"\n=== {node.get_name()} | {node.get_node_title()} ===")
    for pin in node.get_pins():
        lines.append(
            f"  pin {pin.get_name()} dir={pin.get_pin_direction()} cat={pin.get_pin_type().pin_category} linked={pin.is_connected()}"
        )
        if pin.is_connected():
            for link in pin.get_linked_pins():
                owner = link.get_owning_node()
                lines.append(f"    -> {owner.get_name()} | {owner.get_node_title()} :: {link.get_name()}")

# BP_Laser LaserDotTrace visibility branch
laser = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Attachments/Laser/Blueprints/BP_Laser.BP_Laser"
)
for g in unreal.BlueprintEditorLibrary.list_graphs(laser):
    if g.get_name() != "LaserDotTrace":
        continue
    ed2 = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append("\n######## BP_Laser LaserDotTrace ########")
    for node in ed2.list_all_nodes():
        lines.append(f"  {node.get_name()} | {node.get_node_title()}")
        for pin in node.get_pins():
            if pin.is_connected():
                for link in pin.get_linked_pins():
                    owner = link.get_owning_node()
                    lines.append(
                        f"    {node.get_name()}.{pin.get_name()} -> {owner.get_name()}.{link.get_name()}"
                    )

OUT.write_text("\n".join(lines))
unreal.log(f"[probe_setvisibility_aim] wrote {OUT}")
