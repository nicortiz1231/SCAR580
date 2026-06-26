import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_ucs_full.log")
lines = []

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.list_graphs(item)[0]
)
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    if g.get_name() == "UserConstructionScript":
        editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
        break

for node in editor.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    lines.append(f"{node.get_name()} | {title}")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        if pname in ("execute", "then", "self", "NewMesh", "Condition", "Selection"):
            linked = []
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                o = lp.get_owning_node()
                linked.append(f"{o.get_name()}:{pname}")
            try:
                val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                if val:
                    linked.append(val)
            except Exception:
                pass
            if linked:
                lines.append(f"  {pname} -> {linked}")

OUT.write_text("\n".join(lines))
