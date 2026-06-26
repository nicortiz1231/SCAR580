import unreal
from pathlib import Path
OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sniper_after_fix.log")
lines = []
sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
for g in unreal.BlueprintEditorLibrary.list_graphs(sniper):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if any(k in title for k in ("SpawnAttachments", "SetStaticMesh", "SetVisibility")):
            lines.append(f"[{g.get_name()}] {node.get_name()} | {title}")
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                if pn in ("execute", "then", "self", "NewMesh", "bNewVisibility"):
                    linked = []
                    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                        linked.append(lp.get_owning_node().get_name())
                    try:
                        val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                        if val:
                            linked.append(val)
                    except Exception:
                        pass
                    if linked:
                        lines.append(f"  {pn} -> {linked}")
cdo = unreal.get_default_object(sniper.generated_class())
lines.append(f"OpticSightMesh={cdo.get_editor_property('OpticSightMesh').get_name()}")
bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
for handle in sds.k2_gather_subobject_data_for_blueprint(bp):
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle))
    if obj and "FirstPersonCamera" in obj.get_name():
        for prop in ("NearClipPlane", "near_clip_plane"):
            try:
                lines.append(f"camera {prop}={obj.get_editor_property(prop)!r}")
            except Exception:
                pass
OUT.write_text("\n".join(lines))
