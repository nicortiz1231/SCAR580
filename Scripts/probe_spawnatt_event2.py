import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_spawnatt_event2.log")
lines = []

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(item)
)

def walk_exec(start_pin, depth=0, max_depth=40):
    if not start_pin or depth > max_depth:
        return
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(start_pin):
        owner = lp.get_owning_node()
        t = str(owner.get_node_title()).replace("\n", " | ")
        lines.append(f"{'  '*depth}{owner.get_name()} | {t}")
        if owner.get_class().get_name() == "K2Node_SwitchEnum":
            for p in unreal.BlueprintEditorLibrary.list_all_pins(owner):
                pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(p))
                if pn.startswith("NewEnumerator") or pn == "Default":
                    for lp2 in unreal.BlueprintGraphPinLibrary.list_connected_pins(p):
                        o2 = lp2.get_owning_node()
                        lines.append(
                            f"{'  '*(depth+1)}[{pn}] {o2.get_name()} | "
                            f"{str(o2.get_node_title()).replace(chr(10),' | ')}"
                        )
        exec_out = owner.find_then_pin()
        if exec_out:
            walk_exec(exec_out, depth + 1, max_depth)

for node in editor.list_all_nodes():
    if node.get_name() != "K2Node_CustomEvent_3":
        continue
    lines.append("=== SpawnAttachments ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        if pn == "then":
            walk_exec(pin, 0)

# all SwitchEnum on sight in event graph
for node in editor.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    if node.get_class().get_name() != "K2Node_SwitchEnum":
        continue
    if "Sight" not in title and "ENUM_Sights" not in title:
        continue
    lines.append(f"=== switch {node.get_name()} | {title} ===")
    for p in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(p))
        if not pn.startswith("NewEnumerator"):
            continue
        linked = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(p):
            o = lp.get_owning_node()
            linked.append(f"{o.get_name()}:{str(o.get_node_title()).replace(chr(10),' | ')}")
        if linked:
            lines.append(f"  {pn} -> {linked}")

OUT.write_text("\n".join(lines))
