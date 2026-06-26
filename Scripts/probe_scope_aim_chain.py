"""Trace Aim() target component, scope ADS exec chain, and VariableGet_81."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_scope_aim_chain.log")
lines = []

char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))

for name in ("K2Node_VariableGet_81", "K2Node_VariableGet_191", "K2Node_CallFunction_128", "K2Node_CallFunction_144"):
    for node in eg.list_all_nodes():
        if node.get_name() != name:
            continue
        title = str(node.get_node_title()).replace("\n", " | ")
        lines.append(f"\n=== {name} | {title} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            linked = []
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                o = lp.get_owning_node()
                linked.append(f"{o.get_name()}|{str(o.get_node_title()).replace(chr(10),' ')[:40]}")
            if val or linked or pn in ("execute", "then"):
                lines.append(f"  {pn} val={val!r} linked={linked}")

# Walk backward to CallFunction_128 from SwitchEnum_4 NewEnumerator7
def walk_back(exec_pin, depth=0, seen=None):
    if not exec_pin or depth > 20:
        return
    if seen is None:
        seen = set()
    node = exec_pin.get_owning_node()
    nid = node.get_name()
    if nid in seen:
        return
    seen.add(nid)
    lines.append(f"{'  '*depth}<- {nid} | {str(node.get_node_title()).replace(chr(10),' | ')}")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) != unreal.EdGraphPinDirection.EGPD_INPUT:
            continue
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        if pn not in ("execute",):
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            walk_back(lp, depth + 1, seen)

lines.append("\n=== Backward from SwitchEnum_4 NewEnumerator7 exec ===")
for node in eg.list_all_nodes():
    if node.get_name() != "K2Node_SwitchEnum_4":
        continue
    pin = node.find_output_pin("NewEnumerator7")
    if pin:
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            if lp.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT:
                walk_back(lp, 0)

lines.append("\n=== Forward from IfThenElse_17 then/else ===")
ife = None
for n in eg.list_all_nodes():
    if n.get_name() == "K2Node_IfThenElse_17":
        ife = n
        break
if ife:
    for branch in ("then", "else"):
        pin = ife.find_output_pin(branch)
        if not pin:
            continue
        lines.append(f"  {branch}:")
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            o = lp.get_owning_node()
            lines.append(f"    -> {o.get_name()} | {str(o.get_node_title()).replace(chr(10),' | ')}")

# Find Aim function graph on any loaded blueprint
for path in (
    "/Game/BodycamFPSKIT/Blueprints/Components/AC_ProceduralAnimation.AC_ProceduralAnimation",
    "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter",
):
    bp = unreal.load_asset(path)
    if not bp:
        continue
    for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
        if g.get_name() != "Aim":
            continue
        ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
        lines.append(f"\n=== Aim graph on {path.split('/')[-1]} ({len(ed.list_all_nodes())} nodes) ===")
        for n in ed.list_all_nodes():
            t = str(n.get_node_title()).replace("\n", " | ")
            lines.append(f"  {n.get_name()} | {t}")
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(n):
                pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                if val and any(k in pn.lower() for k in ("sight", "gradient", "fov", "on", "off")):
                    lines.append(f"    {pn}={val}")

OUT.write_text("\n".join(lines))
