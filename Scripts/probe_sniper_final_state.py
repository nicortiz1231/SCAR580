import unreal
from pathlib import Path
OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sniper_final_state.log")
lines = []
sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
editor = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(sniper))
for node in editor.list_all_nodes():
    t = str(node.get_node_title()).replace("\n"," | ")
    if any(k in t for k in ("SpawnAttachment","SetStaticMesh","SetVisibility")):
        lines.append(f"sniper: {node.get_name()} | {t}")
item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
editor2 = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(item))
for node in editor2.list_all_nodes():
    if "SpawnAttachments" in str(node.get_node_title()):
        then = node.find_output_pin("then")
        linked = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
            linked.append(str(lp.get_owning_node().get_node_title()).replace("\n"," | "))
        lines.append(f"item SpawnAttachments then -> {linked}")
char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor3 = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))
for node in editor3.list_all_nodes():
    if "SetNearClipPlane" in str(node.get_node_title()):
        lines.append(f"char: {node.get_name()} | SetNearClipPlane")
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
for handle in sds.k2_gather_subobject_data_for_blueprint(sniper):
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle))
    if obj and "OpticSight" in obj.get_name() and obj.get_class().get_name()=="StaticMeshComponent":
        sm = obj.get_editor_property("static_mesh")
        lines.append(f"OpticSight template mesh={sm.get_name() if sm else None}")
OUT.write_text("\n".join(lines))
