"""Dump SetStaticMesh targets for LaserMesh and reload branch conditions."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_laser_setmesh_targets.log")
lines = []

bp = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase"
)
eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(eg)

TARGET_NODES = {
    "K2Node_CallFunction_58", "K2Node_CallFunction_102", "K2Node_CallFunction_117",
    "K2Node_CallFunction_120", "K2Node_CallFunction_57", "K2Node_CallFunction_6",
    "K2Node_CallFunction_132",
}

for node in ed.list_all_nodes():
    if node.get_name() not in TARGET_NODES:
        continue
    lines.append(f"\n{node.get_name()} | {str(node.get_node_title()).replace(chr(10), ' ')}")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        default = ""
        try:
            default = pin.get_default_value()
        except Exception:
            pass
        conns = []
        for cpin in pin.list_connected_pins():
            cn = cpin.get_owning_node()
            conns.append(f"{cn.get_name()}|{str(cn.get_node_title()).replace(chr(10),' ')}")
        if default or conns:
            lines.append(f"  {pname} default={default!r} <- {conns}")

# Reload branch around Event Reload
lines.append("\n=== Reload branch ===")
for node in ed.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " ")
    if node.get_name() in ("K2Node_Event_9", "K2Node_IfThenElse_6", "K2Node_IfThenElse_9", "K2Node_IfThenElse_14"):
        lines.append(f"  {node.get_name()} | {title}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            for cpin in pin.list_connected_pins():
                cn = cpin.get_owning_node()
                ct = str(cn.get_node_title()).replace("\n", " ")
                if "Laser" in ct or "Reload" in ct or "Aim" in ct or "Mesh" in ct:
                    lines.append(f"    {pname} <-> {cn.get_name()} | {ct}")

OUT.write_text("\n".join(lines))
