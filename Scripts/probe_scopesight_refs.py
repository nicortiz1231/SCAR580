"""Search all item/sniper graphs for ScopeSightMesh usage."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_scopesight_refs.log")
lines = []

for path in (
    "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper",
):
    bp = unreal.load_asset(path)
    lines.append(f"=== {path.split('/')[-1]} ===")
    for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
        editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
        for node in editor.list_all_nodes():
            title = str(node.get_node_title()).replace("\n", " | ")
            if not any(k in title for k in ("ScopeSight", "OpticSight", "SetStaticMesh", "SpawnAttachment", "ItemData", "ENUM_Sights")):
                continue
            lines.append(f"  [{g.get_name()}] {node.get_name()} | {title}")

OUT.write_text("\n".join(lines))
