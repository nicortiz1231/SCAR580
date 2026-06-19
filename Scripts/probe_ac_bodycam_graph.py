import unreal
from pathlib import Path
LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_ac_bodycam_graph.log")
lines = []
bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Components/AC_BodycamCamera.AC_BodycamCamera")
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    lines.append(f"graph={g.get_name()}")
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        cls = node.get_class().get_name()
        if cls in ("K2Node_Event", "K2Node_CustomEvent", "K2Node_CallFunction", "K2Node_VariableSet"):
            lines.append(f"  {cls}")
LOG.write_text("\n".join(lines))
