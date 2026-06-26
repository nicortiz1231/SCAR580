"""Verify wheel spawns BP_Weapon_Sniper and optic state."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_deploy_verify.log")
lines = []

char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
ced = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))
for name in ("K2Node_SpawnActorFromClass_1", "K2Node_SpawnActorFromClass_3"):
    for node in ced.list_all_nodes():
        if node.get_name() != name:
            continue
        lines.append(f"=== {name} | {node.get_node_title()} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            linked = [f"{lp.get_owning_node().get_name()}" for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
            if val or (linked and pn == "Class"):
                lines.append(f"  {pn} -> {linked or val}")

sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
for handle in sds.k2_gather_subobject_data_for_blueprint(sniper):
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(
        unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    )
    if obj and "OpticSight" in obj.get_name() and obj.get_class().get_name() == "StaticMeshComponent":
        sm = obj.get_editor_property("static_mesh")
        lines.append(f"SNIPER template OpticSight={sm.get_name() if sm else None}")

cls = sniper.generated_class()
actor = unreal.EditorLevelLibrary.spawn_actor_from_class(cls, unreal.Vector(0,0,1000), unreal.Rotator(0,0,0))
optic = actor.get_editor_property("OpticSight")
sm = optic.get_editor_property("static_mesh") if optic else None
lines.append(f"SNIPER spawned OpticSight={sm.get_name() if sm else None}")
unreal.EditorLevelLibrary.destroy_actor(actor)

# Map_AR default pawn
world = unreal.EditorLevelLibrary.get_editor_world()
lines.append(f"Editor world={world.get_name() if world else None}")

OUT.write_text("\n".join(lines))
