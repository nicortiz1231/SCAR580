"""Test member get OpticSight with item base class path."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_member_get.log")
lines = []

ITEM = "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base_C"
char_bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
)

for class_path in (
    ITEM,
    "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base",
    "BP_Item_Base_C",
):
    try:
        node = editor.add_get_member_variable_node("OpticSight", class_path)
        lines.append(f"OK class_path={class_path!r} node={node.get_name() if node else None}")
        if node:
            editor.remove_nodes([node])
    except Exception as exc:
        lines.append(f"FAIL {class_path!r}: {exc}")

OUT.write_text("\n".join(lines))
