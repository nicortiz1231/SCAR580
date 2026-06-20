"""Dump BeginSetup macro node titles in BP_FPCharacter."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_beginsetup_titles.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if g.get_name() != "BeginSetup":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        try:
            title = node.get_node_title(unreal.NodeTitleType.FULL_TITLE)
        except Exception:
            title = node.get_class().get_name()
        lines.append(f"{node.get_class().get_name()} :: {title}")

OUT.write_text("\n".join(lines))
