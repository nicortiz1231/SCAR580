"""Dump Map_AR level blueprint graph titles."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_map_ar_level_bp.log")
lines = []


def p(msg):
    lines.append(str(msg))
    unreal.log(str(msg))


MAP = "/Game/SCAR580/Maps/Map_AR"
unreal.EditorLoadingAndSavingUtils.load_map(MAP)

cls = unreal.load_class(None, "/Game/SCAR580/Maps/Map_AR.Map_AR_C")
result = unreal.BlueprintEditorLibrary.get_blueprint_for_class(cls)
bp = result[0] if isinstance(result, tuple) else result
p(f"level bp={bp.get_name()}")

for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    nodes = editor.list_all_nodes()
    p(f"graph={g.get_name()} nodes={len(nodes)}")
    for node in nodes:
        try:
            title = node.get_node_title(unreal.NodeTitleType.FULL_TITLE)
        except Exception:
            title = node.get_class().get_name()
        cls_name = node.get_class().get_name()
        if cls_name in (
            "K2Node_Event",
            "K2Node_CustomEvent",
            "K2Node_CallFunction",
            "K2Node_SpawnActorFromClass",
            "K2Node_CreateWidget",
            "K2Node_MacroInstance",
            "K2Node_GetSubsystem",
            "K2Node_GetSubsystemFromPC",
        ):
            p(f"  {node.get_name()} :: {title}")

OUT.write_text("\n".join(lines))
