import unreal
from pathlib import Path
OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_item_all_sight.log")
lines = []
item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        blob = f"{node.get_name()} {title}"
        if any(k.lower() in blob.lower() for k in ("sight", "scope", "optic", "attach", "mesh", "enum_sights")):
            lines.append(f"[{g.get_name()}] {node.get_name()} | {title}")
OUT.write_text("\n".join(lines))
