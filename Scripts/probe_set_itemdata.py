"""Find Set ItemData nodes in item base."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_set_itemdata.log")
lines = []

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if "Set ItemData" in title or "SpawnAttachment" in title:
            lines.append(f"[{g.get_name()}] {node.get_name()} | {title}")

# CallFunction_43/44 on character - what function
bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(bp)
)
for name in ("K2Node_CallFunction_43", "K2Node_CallFunction_44", "K2Node_CallFunction_46"):
    for node in editor.list_all_nodes():
        if node.get_name() != name:
            continue
        lines.append(f"=== {name} | {str(node.get_node_title()).replace(chr(10),' | ')} ===")
        for prop in ("function_reference",):
            try:
                lines.append(f"  {prop}={node.get_editor_property(prop)}")
            except Exception:
                pass

OUT.write_text("\n".join(lines))
