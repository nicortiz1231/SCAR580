"""Find OpticSight mesh assignment in item base."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_optic_mesh.log")
lines = []

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if "SetStaticMesh" in title or "OpticSight" in title or "ScopeSight" in title:
            lines.append(f"[{g.get_name()}] {node.get_name()} | {title}")
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                linked = []
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                    owner = lp.get_owning_node()
                    linked.append(f"{owner.get_name()}:{pname}")
                try:
                    val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                    if val:
                        linked.append(val)
                except Exception:
                    pass
                if linked and pname in ("execute", "self", "NewMesh", "StaticMesh", "then"):
                    lines.append(f"  {pname} -> {linked}")

OUT.write_text("\n".join(lines))
