"""Full diff: SCAR vs Bodycam original sniper + character HandsSlot."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_bodycam_diff.log")
lines = []


def dump_sniper(label, path):
    bp = unreal.load_asset(path)
    if not bp:
        lines.append(f"MISSING {path}")
        return
    cdo = unreal.get_default_object(bp.generated_class())
    lines.append(f"=== {label} CDO ===")
    for prop in ("AimDistanceFromCamera", "ChangeSightSpeed", "ScopeMat_SightDistance",
                 "ScopeMat_GradientParam", "ScopeSightMesh", "OpticSightMesh", "ProceduralValues"):
        try:
            v = cdo.get_editor_property(prop)
            lines.append(f"  {prop}={v.get_path_name() if hasattr(v,'get_path_name') else v}")
        except Exception as e:
            lines.append(f"  {prop} ERR {e}")

    for gname in ("EventGraph", "UserConstructionScript"):
        g = next((g for g in unreal.BlueprintEditorLibrary.list_graphs(bp) if g.get_name() == gname), None)
        if not g:
            continue
        ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
        lines.append(f"=== {label} {gname} ({len(ed.list_all_nodes())} nodes) ===")
        for node in ed.list_all_nodes():
            t = str(node.get_node_title()).replace("\n", " | ")
            lines.append(f"  {node.get_name()} | {t}")
            if "SetStaticMesh" in t:
                for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                    pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                    if pn in ("NewMesh", "self"):
                        linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
                        val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                        lines.append(f"    {pn} -> {linked or val}")

    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    for handle in sds.k2_gather_subobject_data_for_blueprint(bp):
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(
            unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle))
        if obj and "OpticSight" in obj.get_name() and obj.get_class().get_name() == "StaticMeshComponent":
            sm = obj.get_editor_property("static_mesh")
            lines.append(f"  OpticSight.template={sm.get_path_name() if sm else None}")


def dump_hands_slot(char_path, label):
    bp = unreal.load_asset(char_path)
    for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
        if g.get_name() != "BeginSetup":
            continue
        ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
        for node in ed.list_all_nodes():
            if node.get_name() != "K2Node_GenericCreateObject_2":
                continue
            lines.append(f"=== {label} HandsSlot ===")
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                if val and ("ItemData" in pn or pn == "Class"):
                    lines.append(f"  {pn}={val}")

def dump_pickup(path):
    bp = unreal.load_asset(path)
    cdo = unreal.get_default_object(bp.generated_class())
    lines.append(f"=== pickup {path.split('/')[-1]} ===")
    for prop in ("Item Data AttachmentsSight", "Item Data AttachmentsLaser",
                 "Item Data AttachmentsMuzzle", "Item Data Attachments Grip",
                 "Item Data Ammo Count", "Item Data Max Ammo"):
        try:
            lines.append(f"  {prop}={cdo.get_editor_property(prop)!r}")
        except Exception:
            pass

# run in SCAR project context
dump_sniper("SCAR sniper", "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
dump_hands_slot("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter", "SCAR char")
dump_pickup("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Pickup_Sniper.BP_Weapon_Pickup_Sniper")

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
ied = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(item))
for node in ied.list_all_nodes():
    if "SpawnAttachments" in str(node.get_node_title()) and node.get_class().get_name() == "K2Node_CustomEvent":
        then = node.find_output_pin("then")
        linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then)] if then else []
        lines.append(f"item SpawnAttachments then -> {linked or 'NONE'}")

OUT.write_text("\n".join(lines))
