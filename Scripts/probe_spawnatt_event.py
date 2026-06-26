import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_spawnatt_event.log")
lines = []

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(item)
)

for node in editor.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    if "SpawnAttachments" not in title and node.get_name() != "K2Node_CustomEvent_3":
        continue
    lines.append(f"=== {node.get_name()} | {title} ===")
    then = node.find_then_pin() if hasattr(node, "find_then_pin") else None
    if not then and node.get_class().get_name() == "K2Node_CustomEvent":
        then = node.find_pin("then")
    
    stack = [(then, 0)]
    visited = set()
    while stack:
        pin, depth = stack.pop()
        if not pin or depth > 35:
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            owner = lp.get_owning_node()
            nid = owner.get_name()
            if nid in visited and depth > 0:
                continue
            visited.add(nid)
            t = str(owner.get_node_title()).replace("\n", " | ")
            lines.append(f"{'  '*depth}{nid} | {t}")
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
            nxt = owner.find_then_pin() if hasattr(owner, "find_then_pin") else None
            if nxt:
                stack.append((nxt, depth + 1))

OUT.write_text("\n".join(lines))
