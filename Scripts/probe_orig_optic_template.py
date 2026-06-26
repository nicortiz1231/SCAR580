"""Compare original Bodycam sniper OpticSight template vs SCAR."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_orig_optic_template.log")
lines = []

sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
cdo = unreal.get_default_object(sniper.generated_class())
lines.append(f"CDO OpticSightMesh={cdo.get_editor_property('OpticSightMesh').get_path_name()}")
lines.append(f"CDO ScopeSightMesh={cdo.get_editor_property('ScopeSightMesh').get_path_name()}")

sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
for handle in sds.k2_gather_subobject_data_for_blueprint(sniper):
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(
        unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    )
    if not obj or "OpticSight" not in obj.get_name():
        continue
    if obj.get_class().get_name() != "StaticMeshComponent":
        continue
    mesh = obj.get_editor_property("static_mesh")
    hidden = obj.get_editor_property("hidden_in_game")
    vis = obj.get_editor_property("visible")
    lines.append(f"OpticSight component: mesh={mesh.get_name() if mesh else None} hidden_in_game={hidden} visible={vis}")

# Item SpawnAttachments event on disk in BODYCAMFPSKIT - load from original project path
# We're in SCAR project - check item base SpawnAttachments
item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    if g.get_name() != "EventGraph":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        if "SpawnAttachments" not in str(node.get_node_title()):
            continue
        lines.append(f"\nITEM {node.get_name()} | {node.get_node_title()}")
        then = node.find_output_pin("then")
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
            o = lp.get_owning_node()
            lines.append(f"  then -> {o.get_name()} | {o.get_node_title()}")
        # trace full chain
        stack = [(then, 1)]
        while stack:
            pin, depth = stack.pop()
            if not pin or depth > 20:
                continue
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                if lp.get_pin_direction() != unreal.EdGraphPinDirection.EGPD_INPUT:
                    continue
                o = lp.get_owning_node()
                lines.append(f"{'  '*depth}{o.get_name()} | {str(o.get_node_title()).replace(chr(10),' | ')}")
                nxt = o.find_output_pin("then")
                if nxt:
                    stack.append((nxt, depth + 1))

OUT.write_text("\n".join(lines))
