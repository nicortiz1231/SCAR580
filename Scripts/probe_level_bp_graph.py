import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_level_bp_graph.log")
lines = []

def p(msg):
    lines.append(str(msg))
    unreal.log(str(msg))

MAP = "/Game/HandheldAR/Maps/HandheldARBlankMap"
unreal.EditorLoadingAndSavingUtils.load_map(MAP)
cls = unreal.load_class(None, "/Game/HandheldAR/Maps/HandheldARBlankMap.HandheldARBlankMap_C")

result = unreal.BlueprintEditorLibrary.get_blueprint_for_class(cls)
p(f"result type={type(result)} value={result}")

bp = result[0] if isinstance(result, tuple) else result
p(f"bp={bp}")

graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
p(f"graph={graph.get_name()} nodes={len(graph.nodes)}")
for node in graph.nodes:
    title = node.get_node_title(unreal.NodeTitleType.FULL_TITLE)
    p(f"  {node.get_name()} :: {title}")

OUT.write_text("\n".join(lines))
