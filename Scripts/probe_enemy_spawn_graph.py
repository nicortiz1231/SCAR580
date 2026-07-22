"""Probe BlueprintGraphEditor methods and current BP_EnemySpawn graph."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_enemy_spawn_graph.log")
lines = []

def w(msg):
    lines.append(str(msg))
    unreal.log(str(msg))

bp = unreal.load_asset("/Game/FirstPersonHorrorKit/Blueprints/Enemy/BP_EnemySpawn.BP_EnemySpawn")
w(f"bp={bp}")
eg_asset = unreal.BlueprintEditorLibrary.find_event_graph(bp)
w(f"event_graph={eg_asset} name={eg_asset.get_name() if eg_asset else None}")
editor = unreal.BlueprintGraphEditor.get_graph_editor(eg_asset)
w("=== BlueprintGraphEditor methods ===")
for fn in sorted(dir(editor)):
    if fn.startswith("_"):
        continue
    w(fn)

w("=== nodes ===")
for node in editor.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " ")
    w(f"{node.get_name()} | {node.get_class().get_name()} | {title}")

OUT.write_text("\n".join(lines) + "\n")
w(f"wrote {OUT}")
