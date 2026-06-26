import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_spawnatt_body.log")
lines = []

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        if node.get_name() != "K2Node_CustomEvent_3":
            continue
        lines.append(f"graph={g.get_name()}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            linked = []
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                o = lp.get_owning_node()
                linked.append(f"{o.get_name()} | {str(o.get_node_title()).replace(chr(10),' | ')}")
            lines.append(f"  {pn} -> {linked}")

# all graphs SetStaticMesh + OpticSight
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if "SetStaticMesh" in title or ("OpticSight" in title and "Get" in title):
            lines.append(f"[{g.get_name()}] {node.get_name()} | {title}")

OUT.write_text("\n".join(lines))
