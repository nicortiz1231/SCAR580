"""Find where character applies slot ItemData attachments to spawned weapon."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_apply_attachments.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(bp)
)

keywords = (
    "SetStaticMesh", "ScopeSight", "OpticSight", "Set ItemData", "ItemData",
    "Break ST Attachments", "Switch on ENUM_Sights", "SpawnAttachment",
)
for node in editor.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    if not any(k in title for k in keywords):
        continue
    lines.append(f"{node.get_name()} | {title}")

# trace SwitchEnum_3/4 first branch with mesh
for sw in ("K2Node_SwitchEnum_3", "K2Node_SwitchEnum_4"):
    for node in editor.list_all_nodes():
        if node.get_name() != sw:
            continue
        lines.append(f"=== deep {sw} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if pn not in ("NewEnumerator1", "NewEnumerator2", "NewEnumerator4", "NewEnumerator7"):
                continue
            stack = [(pin, 0)]
            while stack:
                p, depth = stack.pop()
                if depth > 8:
                    continue
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(p):
                    o = lp.get_owning_node()
                    t = str(o.get_node_title()).replace("\n", " | ")
                    lines.append(f"{'  '*depth}[{pn}] {o.get_name()} | {t}")
                    if hasattr(o, "find_then_pin"):
                        nxt = o.find_then_pin()
                        if nxt:
                            stack.append((nxt, depth + 1))
                    for p2 in unreal.BlueprintEditorLibrary.list_all_pins(o):
                        pn2 = str(unreal.BlueprintGraphPinLibrary.get_pin_name(p2))
                        if pn2.startswith("NewEnumerator") and o.get_class().get_name() == "K2Node_SwitchEnum":
                            stack.append((p2, depth + 1))

OUT.write_text("\n".join(lines))
