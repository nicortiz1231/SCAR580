import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_opponent_weapon_setup.log")
lines = []

def log(msg):
    lines.append(msg)
    OUT.write_text("\n".join(lines))

BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter"
bp = unreal.load_asset(BP)

for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in ed.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if any(k in title for k in ("Mirror", "CharacterMesh", "ABP_Mirror", "ABP_FP", "ArmsProcedural", "Mesh0")):
            log(f"[{g.get_name()}] {node.get_name()} | {title}")

for name in ("CharacterMesh", "CharacterMesh0"):
    comp = unreal.BlueprintEditorLibrary.get_component_template(bp, name)
    if not comp:
        log(f"TEMPLATE {name}: missing")
        continue
    mesh = comp.get_skeletal_mesh_asset()
    anim = comp.get_editor_property("anim_class")
    log(f"TEMPLATE {name}: mesh={mesh.get_name() if mesh else None} anim={anim.get_name() if anim else None}")

# Inspect pistol item mesh component name
pistol = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Pistol/BP_Weapon_Pistol.BP_Weapon_Pistol")
pcdo = unreal.get_default_object(pistol.generated_class())
for comp in pcdo.get_components_by_class(unreal.ActorComponent.static_class()):
    log(f"PISTOL_COMP {comp.get_name()} {comp.get_class().get_name()}")
