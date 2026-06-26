"""List every item base graph name and search ChangeWeaponSocket on character."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_all_graphs_names.log")
lines = []

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append(f"ITEM {g.get_name()} ({len(editor.list_all_nodes())} nodes)")

char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for g in unreal.BlueprintEditorLibrary.list_graphs(char):
    if "ChangeWeapon" in g.get_name() or "Socket" in g.get_name() or "Attach" in g.get_name() or "Equip" in g.get_name():
        editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
        lines.append(f"CHAR {g.get_name()} ({len(editor.list_all_nodes())} nodes)")

ced = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))
for node in ced.list_all_nodes():
    if "ChangeWeaponSocket" in str(node.get_node_title()):
        lines.append(f"ChangeWeaponSocket node={node.get_name()}")
        ref = None
        try:
            ref = node.get_editor_property("function_reference")
        except Exception:
            pass
        lines.append(f"  ref={ref}")

OUT.write_text("\n".join(lines))
