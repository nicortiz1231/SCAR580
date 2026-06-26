import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_item_setmesh.log")
lines = []

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if "SetStaticMesh" not in title:
            continue
        lines.append(f"[{g.get_name()}] {node.get_name()} | {title}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if pn not in ("self", "NewMesh"):
                continue
            linked = []
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                o = lp.get_owning_node()
                linked.append(f"{o.get_name()} | {str(o.get_node_title()).replace(chr(10),' | ')}")
            if linked:
                lines.append(f"  {pn} -> {linked}")

# character event graph - set mesh on weapon
bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(bp)
)
lines.append("=== character SetStaticMesh ===")
for node in editor.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    if "SetStaticMesh" in title or "ScopeSight" in title or "OpticSight" in title:
        lines.append(f"  {node.get_name()} | {title}")

OUT.write_text("\n".join(lines))
