import unreal
from pathlib import Path
OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_opticsightmesh_refs.log")
lines = []
for path in (
    "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper",
):
    bp = unreal.load_asset(path)
    label = path.split("/")[-1]
    for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
        editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
        for node in editor.list_all_nodes():
            title = str(node.get_node_title()).replace("\n", " | ")
            if any(k in title for k in ("OpticSightMesh", "ScopeSightMesh", "SetStaticMesh", "SpawnAttachment")):
                lines.append(f"[{label}/{g.get_name()}] {node.get_name()} | {title}")
                for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                    pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                    if pn in ("NewMesh", "self", "execute", "then"):
                        linked = []
                        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                            o = lp.get_owning_node()
                            linked.append(str(o.get_node_title()).replace("\n"," | "))
                        if linked:
                            lines.append(f"  {pn} -> {linked}")
OUT.write_text("\n".join(lines))
