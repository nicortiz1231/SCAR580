"""Trace CallFunction_96 SetVisibility -> SpawnActor scope path."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_cf96.log")
lines = []

auto = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase"
)
ed = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(auto)
)

def walk_back_exec(node, depth=0, seen=None):
    if seen is None:
        seen = set()
    if depth > 25 or node.get_name() in seen:
        return
    seen.add(node.get_name())
    title = str(node.get_node_title()).replace("\n", " | ")
    lines.append(f"{'  '*depth}{node.get_name()} | {title}")
    pin = node.find_input_pin("execute")
    if not pin:
        return
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
        walk_back_exec(lp.get_owning_node(), depth + 1, seen)

for target in ("K2Node_CallFunction_96", "K2Node_CallFunction_76", "K2Node_CallFunction_95"):
    for node in ed.list_all_nodes():
        if node.get_name() != target:
            continue
        lines.append(f"\n=== Back from {target} ===")
        walk_back_exec(node)

# forward from Set ScopeRef
for node in ed.list_all_nodes():
    if node.get_name() != "K2Node_VariableSet_13":
        continue
    lines.append("\n=== Forward from Set ScopeRef ===")
    then = node.find_output_pin("then")
    d = 0
    cur = then
    seen = set()
    while cur and d < 15:
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(cur):
            if lp.get_pin_direction() != unreal.EdGraphPinDirection.EGPD_INPUT:
                continue
            o = lp.get_owning_node()
            if o.get_name() in seen:
                continue
            seen.add(o.get_name())
            lines.append(f"{'  '*d}{o.get_name()} | {str(o.get_node_title()).replace(chr(10),' | ')}")
            cur = o.find_output_pin("then")
            d += 1
            break
        else:
            break

OUT.write_text("\n".join(lines))
