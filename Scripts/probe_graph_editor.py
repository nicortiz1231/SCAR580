import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_graph_editor.log")
lines = []

def p(msg):
    lines.append(str(msg))
    unreal.log(str(msg))

bp = unreal.load_asset("/Game/SCAR580/Blueprints/GameModes/GM_SCAR_AR.GM_SCAR_AR")
graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)

p("BlueprintGraphEditor methods:")
for fn in sorted(dir(editor)):
    if not fn.startswith("_"):
        p(f"  {fn}")

p("Existing nodes:")
for node in graph.get_nodes():
    p(f"  {node.get_name()} :: {node.get_node_title(unreal.NodeTitleType.FULL_TITLE)}")

OUT.write_text("\n".join(lines))
