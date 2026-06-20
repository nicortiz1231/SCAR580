"""Verify Map_AR level blueprint nodes after save attempts."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/verify_map_ar_bp.log")
lines = []


def p(msg):
    lines.append(str(msg))
    unreal.log(str(msg))


MAP = "/Game/SCAR580/Maps/Map_AR"
unreal.EditorLoadingAndSavingUtils.load_map(MAP)

cls = unreal.load_class(None, f"{MAP}.Map_AR_C")
level_bp = unreal.BlueprintEditorLibrary.get_blueprint_for_class(cls)
level_bp = level_bp[0] if isinstance(level_bp, tuple) else level_bp
event_graph = unreal.BlueprintEditorLibrary.find_event_graph(level_bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)

nodes = editor.list_all_nodes()
p(f"nodes={len(nodes)}")
for node in nodes:
    cls_name = node.get_class().get_name()
    fn = ""
    if cls_name == "K2Node_CallFunction":
        fn = str(node.get_editor_property("function_reference"))
    p(f"  {node.get_name()} :: {cls_name} :: {fn}")

OUT.write_text("\n".join(lines))
