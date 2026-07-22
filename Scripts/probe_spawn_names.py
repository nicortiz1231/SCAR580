"""Search full available-node catalog for Spawn Actor from Class."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_spawn_names.log")
lines = []

def w(msg):
    lines.append(str(msg))
    unreal.log(str(msg))

bp = unreal.load_asset("/Game/FirstPersonHorrorKit/Blueprints/Enemy/BP_EnemySpawn.BP_EnemySpawn")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(bp))
# empty context = full catalog
avail = [str(x) for x in list(eg.list_available_nodes([]) or [])]
w(f"total={len(avail)}")

exact = [s for s in avail if "spawn actor from class" in s.lower()]
w(f"exact={exact}")

# also look for Gameplay category spawn
gameplay = [s for s in avail if s.lower().startswith("gameplay|") and "spawn" in s.lower()]
w(f"gameplay spawn count={len(gameplay)}")
for s in gameplay[:50]:
    w(f"G {s}")

# any with 'From Class'
from_class = [s for s in avail if "from class" in s.lower()]
w(f"from class count={len(from_class)}")
for s in from_class[:50]:
    w(f"F {s}")

OUT.write_text("\n".join(lines) + "\n")
