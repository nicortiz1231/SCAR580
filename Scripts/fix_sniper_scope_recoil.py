"""Apply sniper 4x scope reliably and reduce recoil mesh clipping."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_sniper_scope_recoil.log")

SNIPER_BP = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper"
CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
SCOPE_MESH = "/Game/BodycamFPSKIT/Demo/Meshes/SM_4xScopeForSniper.SM_4xScopeForSniper"
SET_STATIC_MESH_FN = "/Script/Engine.StaticMeshComponent:SetStaticMesh"
SET_VISIBILITY_FN = "/Script/Engine.SceneComponent:SetVisibility"
NEAR_CLIP = 2.5
SNIPER_ATTACHMENTS = (
    "(Sight_37_688233D743AA415C91250EBC240B11ED=NewEnumerator2,"
    "Laser_38_3209213B48BBF0256E8473A33CC4C0FE=NewEnumerator0,"
    "Muzzle_42_288332C341D7A8B7E31632867A1FE4DB=NewEnumerator0,"
    "Grip_46_62A21AB489496DC33D1ACDA661CA2D84=NewEnumerator5)"
)


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[fix_sniper_scope_recoil] {msg}")


def connect_exec(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def connect_data(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def insert_exec_after_pin(exec_out_pin, new_node) -> bool:
    if not exec_out_pin or not new_node:
        return False
    downstream = []
    for pin in exec_out_pin.list_connected_pins():
        if pin.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT:
            downstream.append(pin)
    exec_in = new_node.find_input_pin("execute")
    exec_out = new_node.find_output_pin("then")
    if not exec_in or not exec_out:
        return False
    if downstream:
        exec_out_pin.break_pin_links()
        if not connect_exec(exec_out_pin, exec_in):
            return False
        for pin in downstream:
            connect_exec(exec_out, pin)
        return True
    return connect_exec(exec_out_pin, exec_in)


def output_pin(node, preferred: str):
    pin = node.find_output_pin(preferred) if hasattr(node, "find_output_pin") else None
    if pin:
        return pin
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) == unreal.EdGraphPinDirection.EGPD_OUTPUT:
            return pin
    return None


def set_pin_value_by_prefix(node, prefix: str, value: str) -> None:
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        if pname.startswith(prefix):
            pin.set_pin_value(value)


def fix_hands_slot(char_bp) -> None:
    for graph in unreal.BlueprintEditorLibrary.list_graphs(char_bp):
        if graph.get_name() != "BeginSetup":
            continue
        editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        for node in editor.list_all_nodes():
            if node.get_name() != "K2Node_GenericCreateObject_2":
                continue
            set_pin_value_by_prefix(node, "ItemData_Attachments", SNIPER_ATTACHMENTS)
            log("HandsSlot sight = NewEnumerator2 (SCOPE)")
            return


def has_spawn_attachments_scope_wiring(editor) -> bool:
    for node in editor.list_all_nodes():
        if node.get_class().get_name() != "K2Node_CustomEvent":
            continue
        if "SpawnAttachments" not in str(node.get_node_title()):
            continue
        then = node.find_output_pin("then")
        if not then:
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
            owner = lp.get_owning_node()
            if "SetStaticMesh" in str(owner.get_node_title()):
                return True
    return False


def wire_scope_apply_nodes(editor, exec_in_pin):
    """Exec chain: SetStaticMesh(scope) -> SetVisibility(true)."""
    set_mesh = editor.add_call_function_node(SET_STATIC_MESH_FN)
    set_vis = editor.add_call_function_node(SET_VISIBILITY_FN)
    get_optic = editor.add_get_member_variable_node("OpticSight")
    if not (set_mesh and set_vis and get_optic):
        raise RuntimeError("Failed creating scope apply nodes")

    if not insert_exec_after_pin(exec_in_pin, set_mesh):
        raise RuntimeError("Failed wiring scope SetStaticMesh exec")
    set_vis_exec = set_mesh.find_output_pin("then")
    connect_exec(set_vis_exec, set_vis.find_input_pin("execute"))

    connect_data(output_pin(get_optic, "OpticSight"), set_mesh.find_input_pin("self"))
    mesh_pin = set_mesh.find_input_pin("NewMesh")
    if mesh_pin:
        mesh_pin.set_pin_value(SCOPE_MESH)

    connect_data(output_pin(get_optic, "OpticSight"), set_vis.find_input_pin("self"))
    vis_pin = set_vis.find_input_pin("bNewVisibility")
    if vis_pin:
        vis_pin.set_pin_value("true")
    new_vis_pin = set_vis.find_input_pin("bNewVisibility")
    if new_vis_pin:
        new_vis_pin.set_pin_value("true")

    return set_vis.find_output_pin("then")


def ensure_sniper_spawn_attachments_override(sniper_bp) -> None:
    event_graph = unreal.BlueprintEditorLibrary.find_event_graph(sniper_bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)
    if has_spawn_attachments_scope_wiring(editor):
        log("Sniper SpawnAttachments override already wired")
        return

    spawn_event = None
    for node in editor.list_all_nodes():
        if node.get_class().get_name() != "K2Node_CustomEvent":
            continue
        if "SpawnAttachments" in str(node.get_node_title()):
            spawn_event = node
            break

    if not spawn_event:
        spawn_event = editor.add_custom_event_node("SpawnAttachments")
    if not spawn_event:
        raise RuntimeError("Could not create SpawnAttachments custom event on sniper")

    then_pin = spawn_event.find_output_pin("then")
    wire_scope_apply_nodes(editor, then_pin)
    log("Wired sniper SpawnAttachments override -> 4x scope mesh")


def ensure_sniper_construction_scope(sniper_bp) -> None:
    ucs = None
    for graph in unreal.BlueprintEditorLibrary.list_graphs(sniper_bp):
        if graph.get_name() == "UserConstructionScript":
            ucs = graph
            break
    if not ucs:
        raise RuntimeError("Sniper UserConstructionScript missing")

    editor = unreal.BlueprintGraphEditor.get_graph_editor(ucs)
    for node in editor.list_all_nodes():
        if node.get_class().get_name() != "K2Node_CallFunction":
            continue
        if "SetStaticMesh" not in str(node.get_node_title()):
            continue
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            if str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin)) == "NewMesh":
                val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                if val and "SM_4xScopeForSniper" in val:
                    log("Sniper Construction Script already sets 4x scope")
                    return

    parent = None
    for node in editor.list_all_nodes():
        if node.get_class().get_name() == "K2Node_CallParentFunction":
            if "Construction Script" in str(node.get_node_title()):
                parent = node
                break
    if not parent:
        raise RuntimeError("Sniper parent construction script missing")

    wire_scope_apply_nodes(editor, parent.find_output_pin("then"))
    log("Wired sniper Construction Script -> 4x scope mesh")


def ensure_sniper_beginplay_scope(sniper_bp) -> None:
    event_graph = unreal.BlueprintEditorLibrary.find_event_graph(sniper_bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)

    parent_begin = None
    begin = editor.find_event_node("ReceiveBeginPlay")
    for node in editor.list_all_nodes():
        if node.get_class().get_name() == "K2Node_CallParentFunction":
            if "BeginPlay" in str(node.get_node_title()):
                parent_begin = node
                break
    if not parent_begin or not begin:
        raise RuntimeError("Sniper BeginPlay chain missing")

    for node in editor.list_all_nodes():
        if node.get_class().get_name() != "K2Node_CallFunction":
            continue
        if "SetStaticMesh" not in str(node.get_node_title()):
            continue
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            if val and "SM_4xScopeForSniper" in val:
                mesh_pin = node.find_input_pin("NewMesh")
                if mesh_pin:
                    mesh_pin.set_pin_value(SCOPE_MESH)
                log("Refreshed sniper BeginPlay scope mesh pin")
                return

    wire_scope_apply_nodes(editor, parent_begin.find_output_pin("then"))
    log("Wired sniper BeginPlay -> 4x scope mesh")


def fix_sniper_cdo_and_component(sniper_bp) -> None:
    scope_mesh = unreal.load_asset(SCOPE_MESH)
    cdo = unreal.get_default_object(sniper_bp.generated_class())
    cdo.set_editor_property("ScopeSightMesh", scope_mesh)
    cdo.set_editor_property("OpticSightMesh", scope_mesh)

    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    seen = set()
    for handle in sds.k2_gather_subobject_data_for_blueprint(sniper_bp):
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
        if not obj or "OpticSight" not in obj.get_name():
            continue
        if obj.get_class().get_name() != "StaticMeshComponent":
            continue
        if id(obj) in seen:
            continue
        seen.add(id(obj))
        obj.set_editor_property("static_mesh", scope_mesh)
        obj.set_editor_property("hidden_in_game", False)
    log("Updated sniper CDO meshes and OpticSight component template")


def insert_post_spawnatt_scope_on_character(char_bp) -> None:
    """Character-side OpticSight access needs a weapon cast; rely on sniper override."""
    log("Skipping character-side SetStaticMesh (sniper SpawnAttachments override handles scope)")


def fix_camera_near_clip(char_bp) -> None:
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    changed = 0
    for handle in sds.k2_gather_subobject_data_for_blueprint(char_bp):
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
        if not obj or "FirstPersonCamera" not in obj.get_name():
            continue
        for prop in ("NearClipPlane", "near_clip_plane"):
            try:
                current = float(obj.get_editor_property(prop))
                if current < NEAR_CLIP - 0.01:
                    obj.set_editor_property(prop, NEAR_CLIP)
                    changed += 1
                    log(f"FirstPersonCamera {prop} {current} -> {NEAR_CLIP}")
                else:
                    log(f"FirstPersonCamera {prop} already {current}")
                break
            except Exception:
                continue
    if not changed:
        log("Could not set camera near clip (property name may differ)")


def tweak_sniper_recoil(sniper_bp) -> None:
    """Reduce backward weapon kick in sniper procedural anim values."""
    cdo = unreal.get_default_object(sniper_bp.generated_class())
    dt = cdo.get_editor_property("ProceduralValues")
    if not dt:
        log("Sniper ProceduralValues missing")
        return

    updated = False
    for prop in sorted(dir(dt)):
        if prop.startswith("_"):
            continue
        lower = prop.lower()
        if not any(k in lower for k in ("weapon", "recoil", "value")):
            continue
        try:
            val = dt.get_editor_property(prop)
        except Exception:
            continue
        if val is None:
            continue

        # WeaponValues / RecoilValues are structs with vector members
        if hasattr(val, "get_editor_property"):
            for sub in sorted(dir(val)):
                if sub.startswith("_"):
                    continue
                sub_lower = sub.lower()
                if not any(k in sub_lower for k in ("recoil", "kick", "loc", "offset", "back")):
                    continue
                try:
                    sub_val = val.get_editor_property(sub)
                except Exception:
                    continue
                if hasattr(sub_val, "x"):
                    x, y, z = float(sub_val.x), float(sub_val.y), float(sub_val.z)
                    # Pull recoil away from camera (positive Y is often toward camera in kit)
                    new_x, new_y, new_z = x * 0.55, y * 0.55, z * 0.85
                    if abs(new_x - x) > 0.01 or abs(new_y - y) > 0.01 or abs(new_z - z) > 0.01:
                        val.set_editor_property(sub, unreal.Vector(new_x, new_y, new_z))
                        updated = True
                        log(f"Reduced {prop}.{sub} ({x},{y},{z}) -> ({new_x},{new_y},{new_z})")
            if updated:
                dt.set_editor_property(prop, val)

    if updated:
        unreal.EditorAssetLibrary.save_asset(dt.get_path_name(), only_if_is_dirty=False)
    else:
        log("No sniper recoil struct fields found to tweak (clip fix uses near plane)")


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    char_bp = unreal.load_asset(f"{CHAR_BP}.BP_FPCharacter")
    sniper_bp = unreal.load_asset(f"{SNIPER_BP}.BP_Weapon_Sniper")
    if not char_bp or not sniper_bp:
        raise RuntimeError("Missing blueprints")

    fix_hands_slot(char_bp)
    insert_post_spawnatt_scope_on_character(char_bp)
    fix_camera_near_clip(char_bp)
    unreal.BlueprintEditorLibrary.compile_blueprint(char_bp)
    unreal.EditorAssetLibrary.save_asset(CHAR_BP, only_if_is_dirty=False)

    ensure_sniper_spawn_attachments_override(sniper_bp)
    ensure_sniper_construction_scope(sniper_bp)
    ensure_sniper_beginplay_scope(sniper_bp)
    fix_sniper_cdo_and_component(sniper_bp)
    tweak_sniper_recoil(sniper_bp)

    sniper_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(sniper_bp)
    unreal.EditorAssetLibrary.save_asset(SNIPER_BP, only_if_is_dirty=False)
    log("Done")


main()
