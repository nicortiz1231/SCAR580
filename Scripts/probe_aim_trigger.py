"""Find what triggers Aim(128) and ScopeRef on sniper ADS."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_aim_trigger.log")
lines = []

char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))

# Full title of VariableGet_81
for node in eg.list_all_nodes():
    if node.get_name() in ("K2Node_VariableGet_81", "K2Node_VariableGet_191", "K2Node_VariableGet_52"):
        lines.append(f"\n=== {node.get_name()} ===")
        lines.append(f"  class={node.get_class().get_name()}")
        lines.append(f"  title={str(node.get_node_title()).replace(chr(10),' | ')}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            d = unreal.BlueprintGraphPinLibrary.get_pin_direction(pin)
            linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
            lines.append(f"  {pn} ({d}) linked={linked}")

# All nodes that connect exec to CallFunction_128
lines.append("\n=== Exec sources to Aim 128 ===")
aim128 = None
for node in eg.list_all_nodes():
    if node.get_name() == "K2Node_CallFunction_128":
        aim128 = node
        break
if aim128:
    pin = aim128.find_input_pin("execute")
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
        src = lp.get_owning_node()
        lines.append(f"  direct exec <- {src.get_name()} | {str(src.get_node_title()).replace(chr(10),' | ')}")

# Forward from SwitchEnum_3 NewEnumerator7
for node in eg.list_all_nodes():
    if node.get_name() != "K2Node_SwitchEnum_3":
        continue
    pin = node.find_output_pin("NewEnumerator7")
    lines.append("\n=== Forward SwitchEnum_3 enum7 ===")
    stack = [(pin, 0)]
    seen = set()
    while stack:
        p, depth = stack.pop()
        if not p or depth > 12:
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(p):
            if lp.get_pin_direction() != unreal.EdGraphPinDirection.EGPD_INPUT:
                continue
            o = lp.get_owning_node()
            nid = o.get_name()
            if nid in seen:
                continue
            seen.add(nid)
            lines.append(f"{'  '*depth}{nid} | {str(o.get_node_title()).replace(chr(10),' | ')}")
            then = o.find_output_pin("then")
            if then:
                stack.append((then, depth + 1))

# Search graphs for "ScopeRef" or "Aim" function on weapon/item
for path in (
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase",
    "/Game/BodycamFPSKIT/Blueprints/Attachments/Scope/Blueprints/BP_Scope",
):
    bp = unreal.load_asset(f"{path}.{path.split('/')[-1]}")
    if not bp:
        continue
    for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
        gname = g.get_name()
        if not any(k in gname for k in ("Aim", "Scope", "Event")):
            continue
        ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
        hits = []
        for n in ed.list_all_nodes():
            t = str(n.get_node_title())
            if any(k in t for k in ("ScopeRef", "Aim", "SightDistance", "Gradient")):
                hits.append(f"  [{gname}] {n.get_name()} | {t.replace(chr(10),' | ')}")
        if hits:
            lines.append(f"\n=== {path.split('/')[-1]} ===")
            lines.extend(hits[:25])

OUT.write_text("\n".join(lines))
