import unreal
from pathlib import Path
OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_macros_sight.log")
lines = []
bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        cls = node.get_class().get_name()
        title = str(node.get_node_title()).replace("\n", " | ")
        if cls == "K2Node_MacroInstance" or "Sight" in title or "Attachment" in title or "Scope" in title:
            if any(k in title for k in ("Macro", "Sight", "Attach", "Scope", "Optic")):
                lines.append(f"[{g.get_name()}] {node.get_name()} | {title}")
                try:
                    lines.append(f"  macro={node.get_editor_property('macro_graph_reference')}")
                except Exception:
                    pass
# item event graph all nodes with Sight/Attach in title
item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if any(k in title for k in ("Sight", "Attach", "Scope", "Optic", "SetStaticMesh")):
            lines.append(f"[item/{g.get_name()}] {node.get_name()} | {title}")
OUT.write_text("\n".join(lines))
