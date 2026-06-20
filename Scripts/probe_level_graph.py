import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_level_graph.log")
lines = []

def p(msg):
    lines.append(str(msg))
    unreal.log(str(msg))

MAP = "/Game/HandheldAR/Maps/HandheldARBlankMap"
unreal.EditorLoadingAndSavingUtils.load_map(MAP)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

# Level script blueprint
for fn in sorted(dir(unreal)):
    if "level" in fn.lower() and "blueprint" in fn.lower():
        p(f"unreal.{fn}")

for fn in sorted(dir(unreal.BlueprintEditorLibrary)):
    if "level" in fn.lower() or "graph" in fn.lower():
        p(f"BEL.{fn}")

try:
    lb = unreal.EditorLevelLibrary.get_level_script_blueprint(world)
    p(f"level blueprint={lb}")
    if lb:
        for graph in lb.get_editor_property("ubergraph_pages"):
            p(f"graph={graph.get_name()} nodes={len(graph.nodes)}")
            for node in graph.nodes:
                p(f"  node {node.get_name()} title={node.get_node_title(unreal.NodeTitleType.FULL_TITLE)}")
except Exception as exc:
    p(f"level bp ERR {exc}")

# ARPassthroughManager actor?
for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor.static_class()):
    cls = actor.get_class().get_name()
    if "AR" in cls or "Passthrough" in cls or "Handheld" in cls:
        p(f"actor {actor.get_name()} :: {cls}")

OUT.write_text("\n".join(lines))
