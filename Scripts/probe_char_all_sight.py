import unreal
from pathlib import Path
OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_char_all_sight.log")
lines = []
bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        blob = f"{title} {node.get_name()}"
        if any(k.lower() in blob.lower() for k in ("sight", "scope", "optic", "setstaticmesh", "enum_sights", "spawnattachment")):
            lines.append(f"[{g.get_name()}] {node.get_name()} | {title}")
OUT.write_text("\n".join(lines))
