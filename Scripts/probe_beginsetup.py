import unreal
from pathlib import Path
LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_beginsetup.log")
lines = []
bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
begin = None
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if g.get_name() == 'BeginSetup':
        begin = g
        break
editor = unreal.BlueprintGraphEditor.get_graph_editor(begin)
for node in editor.list_nodes_of_class(unreal.K2Node_CallFunction.static_class()):
    try:
        ref = node.get_editor_property("function_reference")
        lines.append(str(ref))
    except Exception as exc:
        lines.append(f"ERR {exc}")
LOG.write_text("\n".join(lines))
