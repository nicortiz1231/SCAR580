"""Trace character nodes that set weapon optic mesh from sight enum."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_char_sight_mesh.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(bp)
)

for node in editor.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    if not any(k in title for k in ("SetStaticMesh", "ScopeSight", "OpticSight", "SpawnAttachment")):
        continue
    lines.append(f"{node.get_name()} | {title}")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        if pn in ("self", "NewMesh", "execute", "then"):
            linked = []
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                o = lp.get_owning_node()
                linked.append(f"{o.get_name()} | {str(o.get_node_title()).replace(chr(10),' | ')}")
            if linked:
                lines.append(f"  {pn} -> {linked}")

# walk from SpawnAttachments nodes
for name in ("K2Node_CallFunction_140", "K2Node_CallFunction_141", "K2Node_CallFunction_46"):
    for node in editor.list_all_nodes():
        if node.get_name() != name:
            continue
        lines.append(f"=== chain from {name} ===")
        stack = [(node.find_then_pin(), 0)]
        while stack:
            pin, depth = stack.pop()
            if not pin or depth > 20:
                continue
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                o = lp.get_owning_node()
                t = str(o.get_node_title()).replace("\n", " | ")
                lines.append(f"{'  '*depth}{o.get_name()} | {t}")
                nxt = o.find_then_pin()
                if nxt:
                    stack.append((nxt, depth + 1))

OUT.write_text("\n".join(lines))
