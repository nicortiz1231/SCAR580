"""Exhaustive search for ScopeSightMesh / OpticSightMesh usage in Bodycam weapon hierarchy."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_scope_mesh_usage.log")
lines = []

PATHS = [
    "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_Base.BP_Weapon_Base",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper",
    "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter",
    "/Game/BodycamFPSKIT/Blueprints/Components/BP_ProceduralAnimationComponent.BP_ProceduralAnimationComponent",
]

NEEDLES = ("ScopeSightMesh", "OpticSightMesh", "OpticSight", "SM_4xScope", "SM_SightSniper", "ChangeSight", "ENUM_Sights")

for path in PATHS:
    bp = unreal.load_asset(path)
    if not bp:
        lines.append(f"MISSING {path}")
        continue
    lines.append(f"\n===== {path.split('/')[-1]} =====")
    for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
        ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
        for node in ed.list_all_nodes():
            title = str(node.get_node_title()).replace("\n", " | ")
            blob = f"{node.get_name()} {title}"
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                val = str(unreal.BlueprintGraphPinLibrary.get_pin_value(pin))
                if val:
                    blob += f" [{unreal.BlueprintGraphPinLibrary.get_pin_name(pin)}={val}]"
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                    ot = str(lp.get_owning_node().get_node_title()).replace("\n", " ")
                    blob += f" ->{ot}"
            if any(n in blob for n in NEEDLES):
                lines.append(f"  [{g.get_name()}] {blob[:300]}")

OUT.write_text("\n".join(lines))
