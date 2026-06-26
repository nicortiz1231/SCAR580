import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_setweaponammo.log")
lines = []

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for gname in ("SetWeaponAmmoData", "Fire_HitScan"):
    for g in unreal.BlueprintEditorLibrary.list_graphs(item):
        if g.get_name() != gname:
            continue
        editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
        lines.append(f"=== {gname} ===")
        for node in editor.list_all_nodes():
            title = str(node.get_node_title()).replace("\n", " | ")
            lines.append(f"  {node.get_name()} | {title}")

OUT.write_text("\n".join(lines))
