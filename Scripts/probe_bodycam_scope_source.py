"""Trace how original Bodycam applies optic mesh — UCS, SetWeaponAmmoData, sight switch."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_bodycam_scope_source.log")
lines = []


def w(s=""):
    lines.append(s)


def trace_exec_from(pin, label, max_depth=25):
    w(f"=== {label} ===")
    if not pin:
        w("  (no pin)")
        return
    stack = [(pin, 0)]
    visited = set()
    while stack:
        p, depth = stack.pop()
        if not p or depth > max_depth:
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(p):
            if lp.get_pin_direction() != unreal.EdGraphPinDirection.EGPD_INPUT:
                continue
            node = lp.get_owning_node()
            if id(node) in visited:
                continue
            visited.add(id(node))
            title = str(node.get_node_title()).replace("\n", " | ")
            w(f"{'  '*depth}{node.get_name()} | {title}")
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                if pn in ("NewMesh", "Selection", "Sight", "self", "IsPickUp"):
                    linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
                    val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                    if linked or val:
                        w(f"{'  '*(depth+1)}{pn} -> {linked or val}")
            for branch in ("then", "else"):
                nxt = node.find_output_pin(branch)
                if nxt:
                    stack.append((nxt, depth + 1))


item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")

# UCS full chain
ucs = next(g for g in unreal.BlueprintEditorLibrary.list_graphs(item) if g.get_name() == "UserConstructionScript")
ued = unreal.BlueprintGraphEditor.get_graph_editor(ucs)
w("=== BP_Item_Base UserConstructionScript ALL nodes ===")
for node in ued.list_all_nodes():
    w(f"  {node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')}")

entry = None
for node in ued.list_all_nodes():
    if node.get_class().get_name() == "K2Node_FunctionEntry":
        entry = node
        break
if entry:
    trace_exec_from(entry.find_output_pin("then"), "UCS from FunctionEntry")

# SetWeaponAmmoData full graph
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    if g.get_name() != "SetWeaponAmmoData":
        continue
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    w(f"\n=== SetWeaponAmmoData ALL nodes ({len(ed.list_all_nodes())}) ===")
    for node in ed.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if any(k in title for k in ("Sight", "Optic", "Scope", "Mesh", "Attachment", "Switch", "PickUp", "ItemData", "Spawn")):
            w(f"  {node.get_name()} | {title}")
    for node in ed.list_all_nodes():
        if node.get_class().get_name() != "K2Node_FunctionEntry":
            continue
        trace_exec_from(node.find_output_pin("then"), "SetWeaponAmmoData exec")

# Search all item graphs for sight/scope SetStaticMesh
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in ed.list_all_nodes():
        if "SetStaticMesh" not in str(node.get_node_title()):
            continue
        mesh_pin = node.find_input_pin("NewMesh")
        val = unreal.BlueprintGraphPinLibrary.get_pin_value(mesh_pin) if mesh_pin else ""
        linked = []
        if mesh_pin:
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(mesh_pin):
                linked.append(str(lp.get_owning_node().get_node_title()).replace("\n", " "))
        w(f"[{g.get_name()}] {node.get_name()} NewMesh={linked or val}")

# Character sniper spawn chain in original
char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
ced = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))
for spawn_class_node in ced.list_all_nodes():
    if spawn_class_node.get_class().get_name() != "K2Node_SpawnActorFromClass":
        continue
    cls_pin = spawn_class_node.find_input_pin("Class")
    val = unreal.BlueprintGraphPinLibrary.get_pin_value(cls_pin) if cls_pin else ""
    if val and "Sniper" in val:
        w(f"\n=== Sniper SpawnActor {spawn_class_node.get_name()} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(spawn_class_node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            linked = [f"{lp.get_owning_node().get_name()}:{unreal.BlueprintGraphPinLibrary.get_pin_name(lp)}" for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
            v = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            if linked or v:
                w(f"  {pn} -> {linked or v}")

for name in ("K2Node_VariableSet_15", "K2Node_CallFunction_157", "K2Node_CallFunction_212", "K2Node_CallFunction_141"):
    for node in ced.list_all_nodes():
        if node.get_name() != name:
            continue
        w(f"\n=== CHAR {name} | {str(node.get_node_title()).replace(chr(10),' | ')} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            linked = [f"{lp.get_owning_node().get_name()}:{unreal.BlueprintGraphPinLibrary.get_pin_name(lp)}" for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
            v = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            if linked or v:
                w(f"  {pn} -> {linked or v}")

OUT.write_text("\n".join(lines))
