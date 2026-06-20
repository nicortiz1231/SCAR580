import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_reload_bodycam.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    name = g.get_name()
    if name not in ("ReloadBodycamSettings", "EventGraph", "BeginSetup"):
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append(f"=== {name} ({len(editor.list_all_nodes())} nodes) ===")
    for node in editor.list_all_nodes():
        try:
            title = str(node.get_node_title(unreal.NodeTitleType.FULL_TITLE)).replace("\n", " | ")
        except Exception:
            title = node.get_class().get_name()
        lines.append(f"  {node.get_name()} :: {title}")

OUT.write_text("\n".join(lines))
for line in lines[:80]:
    unreal.log(line)
