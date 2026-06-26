import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sniper_sight_flow.log")
lines = []

for path, label in (
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/AmericanRifle/BP_Weapon_AmericanRifle.BP_Weapon_AmericanRifle",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base",
):
    bp = unreal.load_asset(path)
    lines.append(f"=== {label} ===")
    for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
        editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
        for node in editor.list_all_nodes():
            title = str(node.get_node_title()).replace("\n", " | ")
            if any(k in title for k in ("SetStaticMesh", "ScopeSight", "OpticSight", "SpawnAttachment", "Switch on ENUM_Sights", "Sight")):
                lines.append(f"  [{g.get_name()}] {node.get_name()} | {title}")

OUT.write_text("\n".join(lines))
