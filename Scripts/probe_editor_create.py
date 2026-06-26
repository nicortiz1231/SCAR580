import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_editor_create.log")
lines = []

sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
g = None
for graph in unreal.BlueprintEditorLibrary.list_graphs(sniper):
    if graph.get_name() == "EventGraph":
        g = graph
        break
editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
for fn in sorted(dir(editor)):
    if not fn.startswith("_") and any(k in fn.lower() for k in ("create", "add", "call", "duplicate")):
        lines.append(fn)

OUT.write_text("\n".join(lines))
