import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_spawnatt_all.log")
lines = []

for path, label in (
    ("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base", "ItemBase"),
    ("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper", "Sniper"),
):
    bp = unreal.load_asset(path)
    lines.append(f"=== {label} ===")
    for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
        editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
        for node in editor.list_all_nodes():
            title = str(node.get_node_title()).replace("\n", " | ")
            if "SpawnAttachment" in title or "Spawn Attachment" in title:
                lines.append(f"  [{g.get_name()}] {node.get_name()} | {title}")

OUT.write_text("\n".join(lines))
