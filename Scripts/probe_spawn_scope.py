"""Find what triggers SpawnActor BP_Scope in AutomaticBase."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_spawn_scope.log")
lines = []

auto = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase"
)
ed = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(auto)
)

spawn = None
for node in ed.list_all_nodes():
    if node.get_name() == "K2Node_SpawnActorFromClass_3":
        spawn = node
        break

if spawn:
    lines.append("=== SpawnActor BP_Scope ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(spawn):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
        linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
        lines.append(f"  {pn} val={val!r} linked={linked}")

    # walk back exec
    exec_pin = spawn.find_input_pin("execute")
    depth = 0
    cur = exec_pin
    seen = set()
    while cur and depth < 25:
        o = cur.get_owning_node()
        nid = o.get_name()
        if nid in seen:
            break
        seen.add(nid)
        lines.append(f"  back {depth}: {nid} | {str(o.get_node_title()).replace(chr(10),' | ')}")
        in_exec = o.find_input_pin("execute")
        if not in_exec:
            break
        links = [lp for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(in_exec) if lp.get_pin_direction()==unreal.EdGraphPinDirection.EGPD_OUTPUT or True]
        found = False
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(in_exec):
            prev = lp.get_owning_node()
            if prev.get_name() != nid:
                lines.append(f"  back {depth}: <- {prev.get_name()} | {str(prev.get_node_title()).replace(chr(10),' | ')}")
                in_exec = prev.find_input_pin("execute")
                if in_exec:
                    for lp2 in unreal.BlueprintGraphPinLibrary.list_connected_pins(in_exec):
                        cur = lp2
                        found = True
                        break
                break
        if not found:
            break
        depth += 1

# List all Set ScopeRef
for node in ed.list_all_nodes():
    if "Set ScopeRef" in str(node.get_node_title()):
        lines.append(f"\n=== {node.get_name()} Set ScopeRef ===")
        then = node.find_output_pin("then")
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
            o = lp.get_owning_node()
            lines.append(f"  then -> {o.get_name()} | {str(o.get_node_title()).replace(chr(10),' | ')}")

# Character: wire exec to VariableGet_81?
char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
ceg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))
for node in ceg.list_all_nodes():
    if "K2Node_Knot_4" != node.get_name():
        continue
    lines.append(f"\n=== Knot_4 links ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
        if linked:
            lines.append(f"  {unreal.BlueprintGraphPinLibrary.get_pin_name(pin)} linked={linked}")

OUT.write_text("\n".join(lines))
