"""Deep compare original BODYCAMFPSKIT vs SCAR sniper visuals."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_bodycam_sniper_deep.log")
lines = []


def dump_bp(project_label, uproject_path, sniper_path="/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper"):
    lines.append(f"\n{'='*60}\n=== {project_label} ===\n")
    sniper = unreal.load_asset(f"{sniper_path}.BP_Weapon_Sniper")
    if not sniper:
        lines.append("MISSING sniper bp")
        return
    cdo = unreal.get_default_object(sniper.generated_class())
    for prop in ("AimDistanceFromCamera", "ChangeSightSpeed", "ScopeMat_SightDistance",
                 "ScopeMat_GradientParam", "OpticSightMesh", "ScopeSightMesh", "ProceduralValues"):
        try:
            v = cdo.get_editor_property(prop)
            lines.append(f"CDO {prop}={v.get_path_name() if hasattr(v, 'get_path_name') else v}")
        except Exception as exc:
            lines.append(f"CDO {prop} ERR {exc}")

  # subobjects
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    for handle in sds.k2_gather_subobject_data_for_blueprint(sniper):
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(
            unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        )
        if not obj:
            continue
        name = obj.get_name()
        if any(k in name for k in ("Optic", "Sight", "Scope", "Laser", "Muzzle", "Mesh", "Item")):
            cls = obj.get_class().get_name()
            extra = ""
            if cls == "StaticMeshComponent":
                sm = obj.get_editor_property("static_mesh")
                extra = f" mesh={sm.get_name() if sm else None} hidden={obj.get_editor_property('hidden_in_game')} vis={obj.get_editor_property('visible')}"
            lines.append(f"  COMP {name} ({cls}){extra}")

    for g in unreal.BlueprintEditorLibrary.list_graphs(sniper):
        editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
        hits = []
        for node in editor.list_all_nodes():
            title = str(node.get_node_title()).replace("\n", " | ")
            if any(k in title for k in ("SetStaticMesh", "SetVisibility", "SpawnAttachments", "BeginPlay", "Construction", "OpticSight", "ScopeSight")):
                hits.append(f"  [{g.get_name()}] {node.get_name()} | {title}")
        if hits:
            lines.append(f"GRAPHS {g.get_name()} ({len(editor.list_all_nodes())} nodes):")
            lines.extend(hits)
            # exec chain for SpawnAttachments / BeginPlay
            for node in editor.list_all_nodes():
                t = str(node.get_node_title())
                if "SpawnAttachments" in t or (node.get_name() == "K2Node_Event_0"):
                    lines.append(f"  EXEC from {node.get_name()}:")
                    then = node.find_output_pin("then")
                    if then:
                        stack = [(then, 1)]
                        while stack:
                            pin, depth = stack.pop()
                            if not pin or depth > 12:
                                continue
                            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                                if lp.get_pin_direction() != unreal.EdGraphPinDirection.EGPD_INPUT:
                                    continue
                                o = lp.get_owning_node()
                                lines.append(f"{'  '*depth}{o.get_name()} | {str(o.get_node_title()).replace(chr(10),' | ')}")
                                nxt = o.find_output_pin("then")
                                if nxt:
                                    stack.append((nxt, depth + 1))

    # pickup defaults
    pickup = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Pickup_Sniper.BP_Weapon_Pickup_Sniper")
    if pickup:
        pcdo = unreal.get_default_object(pickup.generated_class())
        for prop in ("Item Data AttachmentsSight", "Item Data AttachmentsLaser", "Item Data AttachmentsMuzzle",
                     "Item Data Ammo Count", "Item Data Max Ammo"):
            try:
                lines.append(f"PICKUP {prop}={pcdo.get_editor_property(prop)}")
            except Exception:
                pass


# Run in SCAR project context first (loads SCAR assets)
dump_bp("SCAR-580", "")

OUT.write_text("\n".join(lines))
print("Wrote", OUT)
