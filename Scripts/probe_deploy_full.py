"""Full deploy diagnostic: spawn path, cooked asset, runtime optic."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_deploy_full.log")
lines = []

# 1) Sniper blueprint state
sniper_path = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper"
sniper = unreal.load_asset(f"{sniper_path}.BP_Weapon_Sniper")
cdo = unreal.get_default_object(sniper.generated_class())
lines.append("=== SNIPER CDO ===")
lines.append(f"  ScopeSightMesh={cdo.get_editor_property('ScopeSightMesh').get_name()}")
lines.append(f"  OpticSightMesh={cdo.get_editor_property('OpticSightMesh').get_name()}")

sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
for handle in sds.k2_gather_subobject_data_for_blueprint(sniper):
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(
        unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    )
    if obj and "OpticSight" in obj.get_name() and obj.get_class().get_name() == "StaticMeshComponent":
        sm = obj.get_editor_property("static_mesh")
        lines.append(f"  template OpticSight={sm.get_name() if sm else 'NONE'}")

# 2) UCS + BeginPlay graphs
for gname in ("UserConstructionScript", "EventGraph"):
    for g in unreal.BlueprintEditorLibrary.list_graphs(sniper):
        if g.get_name() != gname:
            continue
        ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
        scope_nodes = []
        for node in ed.list_all_nodes():
            t = str(node.get_node_title())
            if "SetStaticMesh" in t or "SetVisibility" in t:
                scope_nodes.append(node.get_name())
        lines.append(f"  {gname}: SetStaticMesh nodes={scope_nodes}")

# 3) Spawn test
cls = sniper.generated_class()
actor = unreal.EditorLevelLibrary.spawn_actor_from_class(cls, unreal.Vector(0,0,2000), unreal.Rotator(0,0,0))
optic = actor.get_editor_property("OpticSight")
sm = optic.get_editor_property("static_mesh") if optic else None
lines.append(f"  SPAWNED OpticSight={sm.get_name() if sm else 'NONE'} hidden={optic.get_editor_property('hidden_in_game') if optic else '?'}")
for c in actor.get_components_by_class(unreal.StaticMeshComponent.static_class()):
    m = c.get_editor_property("static_mesh")
    if m:
        lines.append(f"    mesh comp {c.get_name()}={m.get_name()}")
unreal.EditorLevelLibrary.destroy_actor(actor)

# 4) Character sniper spawn chain
char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
ced = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))
for node in ced.list_all_nodes():
    if node.get_name() not in ("K2Node_SpawnActorFromClass_1", "K2Node_VariableSet_15", "K2Node_CallFunction_212", "K2Node_CallFunction_141", "K2Node_CallFunction_157"):
        continue
    lines.append(f"  CHAR {node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')}")
    then = node.find_output_pin("then")
    if then:
        linked = [f"{lp.get_owning_node().get_name()}" for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then)]
        if linked:
            lines.append(f"    then->{linked}")

# 5) HandsSlot weapon class
for g in unreal.BlueprintEditorLibrary.list_graphs(char):
    if g.get_name() != "BeginSetup":
        continue
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in ed.list_all_nodes():
        if node.get_name() != "K2Node_GenericCreateObject_2":
            continue
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            if "WeaponData" in pn or "Attachments" in pn:
                lines.append(f"  HandsSlot {pn}={val}")

# 6) Map_AR game mode
for path in (
    "/Game/SCAR580/Maps/Map_AR",
    "/Game/BodycamFPSKIT/Maps/Map_Test",
):
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        continue
    world = unreal.EditorAssetLibrary.load_asset(path)
    lines.append(f"  MAP exists: {path}")

OUT.write_text("\n".join(lines))
