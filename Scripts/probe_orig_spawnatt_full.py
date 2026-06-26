"""Find SpawnAttachments implementation in item EventGraph - original."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_orig_spawnatt_full.log")
lines = []

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(item))

for node in eg.list_all_nodes():
    if node.get_name() != "K2Node_CustomEvent_3":
        continue
    lines.append("=== SpawnAttachments event ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        linked = [f"{lp.get_owning_node().get_name()}:{unreal.BlueprintGraphPinLibrary.get_pin_name(lp)}" for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
        lines.append(f"  {pn} -> {linked}")
    then = node.find_output_pin("then")
    stack = [(then, 0)]
    while stack:
        pin, depth = stack.pop()
        if not pin or depth > 30:
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

# Search ALL graphs for SetStaticMesh with ScopeSightMesh or 4xScope
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
                linked.append(str(lp.get_owning_node().get_node_title()))
        if "4x" in val or "Scope" in str(linked) or "ScopeSight" in str(linked):
            lines.append(f"[{g.get_name()}] {node.get_name()} mesh={linked or val}")

# char graphs with SetStaticMesh on spawned weapon optic
char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for g in unreal.BlueprintEditorLibrary.list_graphs(char):
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in ed.list_all_nodes():
        if "SetStaticMesh" not in str(node.get_node_title()):
            continue
        lines.append(f"[CHAR/{g.get_name()}] {node.get_name()} | {node.get_node_title()}")

OUT.write_text("\n".join(lines))
