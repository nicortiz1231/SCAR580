"""List available BlueprintGraphEditor nodes and create SpawnActor by name."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_available_nodes.log")
lines = []

def w(msg):
    lines.append(str(msg))
    unreal.log(str(msg))

bp = unreal.load_asset("/Game/FirstPersonHorrorKit/Blueprints/Enemy/BP_EnemySpawn.BP_EnemySpawn")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(bp))

avail = eg.list_available_nodes()
w(f"available count={len(avail) if avail is not None else None} type={type(avail)}")
# avail might be array of strings or structs
items = list(avail) if avail is not None else []
spawnish = []
for item in items:
    s = str(item)
    if any(k in s.lower() for k in ("spawn", "actor", "transform", "self", "get actor")):
        spawnish.append(s)
w(f"spawnish={len(spawnish)}")
for s in spawnish[:80]:
    w(s)

# Try create_node_from_name candidates
candidates = [
    "SpawnActorFromClass",
    "Spawn Actor from Class",
    "K2Node_SpawnActorFromClass",
    "SpawnActor",
    "Spawn Actor",
]
for name in candidates:
    try:
        node = eg.create_node_from_name(name)
        w(f"create_node_from_name({name!r}) -> {node} ({node.get_name() if node else None})")
        if node:
            break
    except Exception as exc:
        w(f"create_node_from_name({name!r}) ERR {exc}")

OUT.write_text("\n".join(lines) + "\n")
w(f"wrote {OUT}")
