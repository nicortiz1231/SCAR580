import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_item_graphs2.log")
lines = []

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
lines.append("=== graphs ===")
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    lines.append(f"  {g.get_name()}")

for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    if "Spawn" not in g.get_name() and "Sight" not in g.get_name() and "Attach" not in g.get_name():
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append(f"=== {g.get_name()} ({len(editor.list_all_nodes())} nodes) ===")
    for node in editor.list_all_nodes()[:40]:
        lines.append(f"  {node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')}")

# UserConstructionScript optic flow
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    if g.get_name() != "UserConstructionScript":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append("=== UserConstructionScript optic chain ===")
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if any(k in title for k in ("Optic", "Scope", "SetStaticMesh", "Sight", "Item Data")):
            lines.append(f"  {node.get_name()} | {title}")

OUT.write_text("\n".join(lines))
