"""Find sight mesh application graphs in item base and sniper."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sight_graphs.log")
lines = []

for path, label in (
    "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper",
):
    bp = unreal.load_asset(path)
    lines.append(f"=== {label} graphs ===")
    for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
        gname = g.get_name()
        editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
        hits = []
        for node in editor.list_all_nodes():
            title = str(node.get_node_title()).replace("\n", " | ")
            if any(k in title for k in ("ENUM_Sights", "ScopeSight", "OpticSightMesh", "SetStaticMesh", "Switch", "Akimbo")):
                hits.append(f"  {node.get_name()} | {title}")
        if hits:
            lines.append(f"[{gname}] ({len(hits)} hits)")
            lines.extend(hits[:30])

OUT.write_text("\n".join(lines))
