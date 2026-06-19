import unreal
from pathlib import Path
LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_bp_graph.log")
bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
begin = None
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if g.get_name() == 'BeginSetup':
        begin = g
        break
editor = unreal.BlueprintGraphEditor.get_graph_editor(begin)
methods = [m for m in dir(editor) if not m.startswith('_')]
LOG.write_text("\n".join(methods))
