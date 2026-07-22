"""Probe create_node_from_name / list_available_nodes signatures and create SpawnActor."""
import unreal
from pathlib import Path
import inspect

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_create_spawn.log")
lines = []

def w(msg):
    lines.append(str(msg))
    unreal.log(str(msg))

bp = unreal.load_asset("/Game/FirstPersonHorrorKit/Blueprints/Enemy/BP_EnemySpawn.BP_EnemySpawn")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(bp))

for name in ("list_available_nodes", "create_node_from_name", "call_method"):
    fn = getattr(eg, name, None)
    w(f"{name} -> {fn}")
    try:
        w(f"  doc={getattr(fn, '__doc__', None)}")
    except Exception:
        pass
    try:
        w(f"  sig={inspect.signature(fn)}")
    except Exception as exc:
        w(f"  sig ERR {exc}")

# Try create_node_from_name with common names
candidates = [
    "Spawn Actor from Class",
    "SpawnActorFromClass",
    "K2Node_SpawnActorFromClass",
    "Spawn Actor",
    "SpawnActor",
]
for name in candidates:
    try:
        node = eg.create_node_from_name(name)
        w(f"OK create_node_from_name({name!r}) -> {node.get_name() if node else None} cls={node.get_class().get_name() if node else None}")
        if node:
            break
    except Exception as exc:
        w(f"ERR create_node_from_name({name!r}): {exc}")

# Try list_available_nodes with empty pins
begin = None
for node in eg.list_all_nodes():
    if "BeginPlay" in str(node.get_node_title()):
        begin = node
        break
pins = []
if begin:
    pins = list(unreal.BlueprintEditorLibrary.list_all_pins(begin))
    w(f"begin pins={len(pins)}")

for args in (
    ([],),
    (pins,),
    (None,),
):
    try:
        avail = eg.list_available_nodes(*args)
        w(f"list_available_nodes{args} -> type={type(avail)} len={len(list(avail)) if avail is not None else None}")
        if avail:
            matched = [str(x) for x in list(avail) if "spawn" in str(x).lower()]
            w(f"  spawn matches={matched[:20]}")
            break
    except Exception as exc:
        w(f"list_available_nodes{args} ERR {exc}")

OUT.write_text("\n".join(lines) + "\n")
w(f"wrote {OUT}")
