"""Find Akimbo Spawner callers and sight mesh apply in item BP."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_akimbo_caller.log")
lines = []

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")

# who calls Akimbo Spawner
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if "Akimbo Spawner" in title or title == "Akimbo Spawner":
            lines.append(f"CALL [{g.get_name()}] {node.get_name()} | {title}")
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                if pn in ("execute", "then"):
                    linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
                    if linked:
                        lines.append(f"  {pn} -> {linked}")

# full Akimbo Spawner graph exec + sight switch
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    if g.get_name() != "Akimbo Spawner":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append("\n=== Akimbo Spawner full exec from entry ===")
    entry = None
    for node in editor.list_all_nodes():
        if node.get_class().get_name() == "K2Node_FunctionEntry":
            entry = node
            break
    stack = [(entry.find_output_pin("then"), 0)]
    while stack:
        pin, depth = stack.pop()
        if not pin or depth > 50:
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            if lp.get_pin_direction() != unreal.EdGraphPinDirection.EGPD_INPUT:
                continue
            o = lp.get_owning_node()
            t = str(o.get_node_title()).replace("\n", " | ")
            lines.append(f"{'  '*depth}{o.get_name()} | {t}")
            if o.get_class().get_name() == "K2Node_SwitchEnum":
                for p in unreal.BlueprintEditorLibrary.list_all_pins(o):
                    pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(p))
                    if pn.startswith("NewEnumerator"):
                        for lp2 in unreal.BlueprintGraphPinLibrary.list_connected_pins(p):
                            o2 = lp2.get_owning_node()
                            lines.append(f"{'  '*(depth+1)}[{pn}] {o2.get_name()} | {str(o2.get_node_title()).replace(chr(10),' | ')}")
            nxt = o.find_output_pin("then")
            if nxt:
                stack.append((nxt, depth + 1))

# character calls to item functions with Sight/Attach
char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
ced = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))
lines.append("\n=== CHAR calls with Attach/Sight/Akimbo ===")
for node in ced.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    if any(k in title for k in ("Akimbo", "Attachment", "Sight", "Scope", "SetStaticMesh")):
        lines.append(f"{node.get_name()} | {title}")

OUT.write_text("\n".join(lines))
