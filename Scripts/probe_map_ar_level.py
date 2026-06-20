import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_map_ar_level.log")
lines = []


def p(msg):
    lines.append(str(msg))
    unreal.log(str(msg))


MAP = "/Game/SCAR580/Maps/Map_AR"
unreal.EditorLoadingAndSavingUtils.load_map(MAP)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

ws = world.get_world_settings()
p(f"world default_game_mode={ws.get_editor_property('default_game_mode')}")

cls = unreal.load_class(None, "/Game/SCAR580/Maps/Map_AR.Map_AR_C")
result = unreal.BlueprintEditorLibrary.get_blueprint_for_class(cls)
bp = result[0] if isinstance(result, tuple) else result
graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)

nodes = graph.get_nodes() if hasattr(graph, "get_nodes") else graph.get_editor_property("nodes")
p(f"Map_AR level BP graph nodes={len(nodes)}")
for node in nodes:
    title = node.get_node_title(unreal.NodeTitleType.FULL_TITLE)
    p(f"  {node.get_name()} :: {title}")

# Check spawned pawn-related actors in editor world
for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor.static_class()):
    label = actor.get_actor_label()
    cls_name = actor.get_class().get_name()
    if any(k in cls_name for k in ("Light", "Player", "AR", "Character", "Pawn", "HUD", "PostProcess")):
        hidden = actor.get_actor_hidden_in_game()
        p(f"actor {label} ({cls_name}) hidden_in_game={hidden}")

OUT.write_text("\n".join(lines))
