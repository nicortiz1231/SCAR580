"""Trace how stock Bodycam applies sniper scope on pickup vs wheel spawn."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_scope_pickup_flow.log")
lines = []


def pin_links(node, pin_names):
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        if pn not in pin_names:
            continue
        linked = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            o = lp.get_owning_node()
            linked.append(f"{o.get_name()}:{pn}")
        val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
        if linked or val:
            lines.append(f"    {pn} -> {linked or val}")


item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if not any(k in title for k in (
            "ScopeSight", "OpticSight", "SetStaticMesh", "ENUM_Sights",
            "SpawnAttachment", "Akimbo", "ItemData", "Sight",
        )):
            continue
        lines.append(f"[{g.get_name()}] {node.get_name()} | {title}")
        pin_links(node, ("execute", "then", "NewMesh", "Selection", "Condition", "self", "Sight"))

sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
cdo = unreal.get_default_object(sniper.generated_class())
for prop in ("ScopeSightMesh", "OpticSightMesh", "AimDistanceFromCamera"):
    val = cdo.get_editor_property(prop)
    lines.append(f"sniper.{prop}={val.get_path_name() if hasattr(val,'get_path_name') else val}")

sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
for handle in sds.k2_gather_subobject_data_for_blueprint(sniper):
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(
        unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    )
    if obj and "OpticSight" in obj.get_name() and obj.get_class().get_name() == "StaticMeshComponent":
        sm = None
        try:
            sm = obj.get_editor_property("static_mesh")
        except Exception:
            pass
        lines.append(f"OpticSight template static_mesh={sm.get_path_name() if sm else None}")

# character equip SpawnAttachments chain
char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
ced = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))
for name in ("K2Node_CallFunction_46", "K2Node_CallFunction_140", "K2Node_CallFunction_17"):
    for node in ced.list_all_nodes():
        if node.get_name() != name:
            continue
        lines.append(f"=== char {name} | {str(node.get_node_title()).replace(chr(10),' | ')} ===")
        pin_links(node, ("execute", "then", "self"))

OUT.write_text("\n".join(lines))
