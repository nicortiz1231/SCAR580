"""Trace exec into SpawnActor BP_Scope."""
import unreal
from pathlib import Path

auto = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(auto))
spawn = next(n for n in eg.list_all_nodes() if n.get_name() == "K2Node_SpawnActorFromClass_3")
lines = []
lines.append(f"=== {spawn.get_node_title()} ===")
exec_in = spawn.find_input_pin("execute")
for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(exec_in):
    o = lp.get_owning_node()
    lines.append(f"exec from {o.get_name()} | {o.get_node_title()}")
    # walk back
    stack = [o]
    seen = set()
    for depth in range(10):
        if not stack:
            break
        node = stack.pop()
        if id(node) in seen:
            continue
        seen.add(id(node))
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) != unreal.EdGraphPinDirection.EGPD_INPUT:
                continue
            if unreal.BlueprintGraphPinLibrary.get_pin_name(pin) not in ("execute", "Condition", "Selection"):
                continue
            for lp2 in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                prev = lp2.get_owning_node()
                lines.append(f"{'  '*(depth+1)}{prev.get_name()} | {prev.get_node_title()} [{unreal.BlueprintGraphPinLibrary.get_pin_name(pin)}]")
                stack.append(prev)

# SetStaticMesh 76 mesh source
for n in eg.list_all_nodes():
    if n.get_name() != "K2Node_CallFunction_76":
        continue
    lines.append("=== SetStaticMesh 76 ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(n):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        linked = [str(lp.get_owning_node().get_node_title()) for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
        val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
        if linked or val:
            lines.append(f"  {pn}={linked or val}")

Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_bp_scope_spawn.log").write_text("\n".join(lines))
