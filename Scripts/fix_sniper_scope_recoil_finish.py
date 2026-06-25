"""Finish scope visibility + reduce recoil clipping without changing ADS distance."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_sniper_scope_recoil_finish.log")

CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
ITEM_BP = "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base"
SNIPER_BP = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper"
SCOPE_MESH = "/Game/BodycamFPSKIT/Demo/Meshes/SM_4xScopeForSniper.SM_4xScopeForSniper"
SET_STATIC_MESH_FN = "/Script/Engine.StaticMeshComponent:SetStaticMesh"
SET_VISIBILITY_FN = "/Script/Engine.SceneComponent:SetVisibility"
SET_NEAR_CLIP_FN = "/Script/Engine.CameraComponent:SetNearClipPlane"
NEAR_CLIP = 3.0


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[fix_sniper_finish] {msg}")


def connect_exec(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def connect_data(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def output_pin(node, preferred: str):
    pin = node.find_output_pin(preferred) if hasattr(node, "find_output_pin") else None
    if pin:
        return pin
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) == unreal.EdGraphPinDirection.EGPD_OUTPUT:
            return pin
    return None


def wire_scope_on_exec(editor, exec_in_pin):
    set_mesh = editor.add_call_function_node(SET_STATIC_MESH_FN)
    set_vis = editor.add_call_function_node(SET_VISIBILITY_FN)
    get_optic = editor.add_get_member_variable_node("OpticSight")
    if not all((set_mesh, set_vis, get_optic)):
        raise RuntimeError("Failed creating scope nodes")

    optic_out = output_pin(get_optic, "OpticSight")
    connect_data(optic_out, set_mesh.find_input_pin("self"))
    connect_data(optic_out, set_vis.find_input_pin("self"))

    mesh_pin = set_mesh.find_input_pin("NewMesh")
    if mesh_pin:
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(mesh_pin):
            lp.break_pin_links()
        mesh_pin.set_pin_value(SCOPE_MESH)

    vis_pin = set_vis.find_input_pin("bNewVisibility")
    if vis_pin:
        vis_pin.set_pin_value("true")

    downstream = []
    if exec_in_pin:
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(exec_in_pin):
            if lp.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT:
                downstream.append(lp)
        if downstream:
            exec_in_pin.break_pin_links()
            connect_exec(exec_in_pin, set_mesh.find_input_pin("execute"))
            connect_exec(set_mesh.find_output_pin("then"), set_vis.find_input_pin("execute"))
            for pin in downstream:
                connect_exec(set_vis.find_output_pin("then"), pin)
        else:
            connect_exec(exec_in_pin, set_mesh.find_input_pin("execute"))
            connect_exec(set_mesh.find_output_pin("then"), set_vis.find_input_pin("execute"))

    return set_vis.find_output_pin("then")


def ensure_item_spawnattachments(item_bp) -> None:
    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(item_bp)
    )
    for node in editor.list_all_nodes():
        if node.get_class().get_name() != "K2Node_CustomEvent":
            continue
        if "SpawnAttachments" not in str(node.get_node_title()):
            continue
        then = node.find_output_pin("then")
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
            if "SetStaticMesh" in str(lp.get_owning_node().get_node_title()):
                log("Item SpawnAttachments already wired")
                return
        wire_scope_on_exec(editor, then)
        log("Wired item SpawnAttachments -> 4x scope")
        return
    raise RuntimeError("Item SpawnAttachments event missing")


def ensure_sniper_spawnattachments(sniper_bp) -> None:
    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(sniper_bp)
    )
    spawn_event = None
    for node in editor.list_all_nodes():
        if node.get_class().get_name() not in ("K2Node_CustomEvent", "K2Node_Event"):
            continue
        if "SpawnAttachments" not in str(node.get_node_title()):
            continue
        spawn_event = node
        break
    if not spawn_event:
        spawn_event = editor.add_custom_event_node("SpawnAttachments")
    then = spawn_event.find_output_pin("then")
    if then:
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
            if "SetStaticMesh" in str(lp.get_owning_node().get_node_title()):
                log("Sniper SpawnAttachments already wired")
                return
    wire_scope_on_exec(editor, then)
    log("Wired sniper SpawnAttachments override -> 4x scope")


def refresh_sniper_ucs_beginplay(sniper_bp) -> None:
    scope_mesh = unreal.load_asset(SCOPE_MESH)
    for graph_name in ("UserConstructionScript", "EventGraph"):
        graph = None
        for g in unreal.BlueprintEditorLibrary.list_graphs(sniper_bp):
            if g.get_name() == graph_name:
                graph = g
                break
        if not graph:
            continue
        editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        parent = None
        for node in editor.list_all_nodes():
            if node.get_class().get_name() != "K2Node_CallParentFunction":
                continue
            title = str(node.get_node_title())
            if graph_name == "UserConstructionScript" and "Construction Script" in title:
                parent = node
            if graph_name == "EventGraph" and "BeginPlay" in title:
                parent = node
        if not parent:
            continue

        set_mesh = None
        set_vis = None
        for node in editor.list_all_nodes():
            if node.get_class().get_name() != "K2Node_CallFunction":
                continue
            title = str(node.get_node_title())
            if "SetStaticMesh" in title:
                set_mesh = node
            if "SetVisibility" in title:
                set_vis = node

        if not set_mesh:
            wire_scope_on_exec(editor, parent.find_output_pin("then"))
            log(f"Created scope chain in sniper {graph_name}")
            continue

        mesh_pin = set_mesh.find_input_pin("NewMesh")
        if mesh_pin:
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(mesh_pin):
                lp.break_pin_links()
            mesh_pin.set_pin_value(SCOPE_MESH)

        if not set_vis:
            set_vis = editor.add_call_function_node(SET_VISIBILITY_FN)
            get_optic = editor.add_get_member_variable_node("OpticSight")
            connect_data(output_pin(get_optic, "OpticSight"), set_vis.find_input_pin("self"))
            vis_pin = set_vis.find_input_pin("bNewVisibility")
            if vis_pin:
                vis_pin.set_pin_value("true")
            connect_exec(set_mesh.find_output_pin("then"), set_vis.find_input_pin("execute"))

        parent_then = parent.find_output_pin("then")
        if parent_then:
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(parent_then):
                if lp.get_owning_node() == set_mesh:
                    break
            else:
                parent_then.break_pin_links()
                connect_exec(parent_then, set_mesh.find_input_pin("execute"))

        log(f"Refreshed sniper {graph_name} scope + visibility")

    cdo = unreal.get_default_object(sniper_bp.generated_class())
    cdo.set_editor_property("ScopeSightMesh", scope_mesh)
    cdo.set_editor_property("OpticSightMesh", scope_mesh)

    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    seen = set()
    for handle in sds.k2_gather_subobject_data_for_blueprint(sniper_bp):
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(
            unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        )
        if not obj or "OpticSight" not in obj.get_name():
            continue
        if obj.get_class().get_name() != "StaticMeshComponent":
            continue
        if id(obj) in seen:
            continue
        seen.add(id(obj))
        obj.set_editor_property("static_mesh", scope_mesh)
        obj.set_editor_property("hidden_in_game", False)
        try:
            obj.set_editor_property("visible", True)
        except Exception:
            pass
    log("Updated OpticSight component template mesh + visibility")


def tweak_recoil_values(sniper_bp) -> None:
    cdo = unreal.get_default_object(sniper_bp.generated_class())
    pv = cdo.get_editor_property("ProceduralValues")
    if not pv:
        return

    updated = False
    for block_name in ("WeaponValues", "RecoilValues"):
        try:
            block = pv.get_editor_property(block_name)
        except Exception:
            continue
        if not block:
            continue
        for prop in (
            "BasePoseLoc", "BasePoseRot", "RecoilLoc", "RecoilRot",
            "RecoilTranslation", "RecoilRotation", "Kickback", "Kick",
        ):
            try:
                val = block.get_editor_property(prop)
            except Exception:
                continue
            if not hasattr(val, "x"):
                continue
            x, y, z = float(val.x), float(val.y), float(val.z)
            # Reduce motion toward camera (Y/Z axes used by kit for kickback).
            new = unreal.Vector(x * 0.75, y * 0.70, z * 0.80)
            if abs(new.x - x) > 0.01 or abs(new.y - y) > 0.01 or abs(new.z - z) > 0.01:
                block.set_editor_property(prop, new)
                updated = True
                log(f"Reduced {block_name}.{prop} ({x:.2f},{y:.2f},{z:.2f}) -> ({new.x:.2f},{new.y:.2f},{new.z:.2f})")

        if updated:
            pv.set_editor_property(block_name, block)

    if updated:
        pv.modify()
        unreal.EditorAssetLibrary.save_asset(pv.get_path_name(), only_if_is_dirty=False)


def wire_camera_near_clip_on_beginplay(char_bp) -> None:
    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
    )
    for node in editor.list_all_nodes():
        if node.get_class().get_name() != "K2Node_CallFunction":
            continue
        if "SetNearClipPlane" not in str(node.get_node_title()):
            continue
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            if val and float(val.split()[0] if " " in val else val) >= NEAR_CLIP - 0.1:
                log("BeginPlay near clip already wired")
                return

    begin = editor.find_event_node("ReceiveBeginPlay")
    if not begin:
        return

    set_clip = editor.add_call_function_node(SET_NEAR_CLIP_FN)
    get_cam = editor.add_get_member_variable_node("FirstPersonCamera")
    if not set_clip or not get_cam:
        log("Could not create near clip nodes")
        return

    connect_data(output_pin(get_cam, "FirstPersonCamera"), set_clip.find_input_pin("self"))
    clip_pin = set_clip.find_input_pin("NearClipPlane")
    if clip_pin:
        clip_pin.set_pin_value(str(NEAR_CLIP))

    begin_then = begin.find_then_pin()
    if not begin_then:
        return
    downstream = None
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(begin_then):
        downstream = lp
        break
    begin_then.break_pin_links()
    connect_exec(begin_then, set_clip.find_input_pin("execute"))
    if downstream:
        connect_exec(set_clip.find_output_pin("then"), downstream)
    log(f"Wired BeginPlay -> SetNearClipPlane({NEAR_CLIP})")


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    char_bp = unreal.load_asset(f"{CHAR_BP}.BP_FPCharacter")
    item_bp = unreal.load_asset(f"{ITEM_BP}.BP_Item_Base")
    sniper_bp = unreal.load_asset(f"{SNIPER_BP}.BP_Weapon_Sniper")
    if not all((char_bp, item_bp, sniper_bp)):
        raise RuntimeError("Missing blueprints")

    try:
        ensure_item_spawnattachments(item_bp)
        unreal.BlueprintEditorLibrary.compile_blueprint(item_bp)
        unreal.EditorAssetLibrary.save_asset(ITEM_BP, only_if_is_dirty=False)
    except Exception as exc:
        log(f"Item SpawnAttachments: {exc}")

    ensure_sniper_spawnattachments(sniper_bp)
    refresh_sniper_ucs_beginplay(sniper_bp)
    tweak_recoil_values(sniper_bp)
    sniper_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(sniper_bp)
    unreal.EditorAssetLibrary.save_asset(SNIPER_BP, only_if_is_dirty=False)

    wire_camera_near_clip_on_beginplay(char_bp)
    unreal.BlueprintEditorLibrary.compile_blueprint(char_bp)
    unreal.EditorAssetLibrary.save_asset(CHAR_BP, only_if_is_dirty=False)
    log("Done")


main()
