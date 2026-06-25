"""Remove broken character scope wiring and implement item SpawnAttachments."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_sniper_scope_final.log")

CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
ITEM_BP = "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base"
SNIPER_BP = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper"
SCOPE_MESH = "/Game/BodycamFPSKIT/Demo/Meshes/SM_4xScopeForSniper.SM_4xScopeForSniper"
SET_STATIC_MESH_FN = "/Script/Engine.StaticMeshComponent:SetStaticMesh"
SET_VISIBILITY_FN = "/Script/Engine.SceneComponent:SetVisibility"
SNIPER_ATTACHMENTS = (
    "(Sight_37_688233D743AA415C91250EBC240B11ED=NewEnumerator2,"
    "Laser_38_3209213B48BBF0256E8473A33CC4C0FE=NewEnumerator0,"
    "Muzzle_42_288332C341D7A8B7E31632867A1FE4DB=NewEnumerator0,"
    "Grip_46_62A21AB489496DC33D1ACDA661CA2D84=NewEnumerator5)"
)
SPAWN_ATT_NAMES = ("K2Node_CallFunction_140", "K2Node_CallFunction_141")


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[fix_sniper_final] {msg}")


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


def insert_exec_after(exec_out_pin, new_node, downstream_exec_pin) -> bool:
    exec_in = new_node.find_input_pin("execute")
    exec_out = new_node.find_output_pin("then")
    if not exec_in or not exec_out:
        return False
    exec_out_pin.break_pin_links()
    if not connect_exec(exec_out_pin, exec_in):
        return False
    if downstream_exec_pin:
        return connect_exec(exec_out, downstream_exec_pin)
    return True


def cleanup_character_scope_nodes(char_bp) -> None:
    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
    )
    remove = []
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " ")
        cls = node.get_class().get_name()
        if "ScopeSightMesh" in title or "SM_4xScopeForSniper" in title:
            remove.append(node)
        if cls == "K2Node_IfThenElse" and "Branch" in title:
            # remove scope branches wired directly from spawn att
            for spawn_name in SPAWN_ATT_NAMES:
                spawn_att = None
                for n in editor.list_all_nodes():
                    if n.get_name() == spawn_name:
                        spawn_att = n
                        break
                if not spawn_att:
                    continue
                then = spawn_att.find_output_pin("then")
                if not then:
                    continue
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
                    if lp.get_owning_node() == node:
                        remove.append(node)
        if cls == "K2Node_CallFunction":
            if "EqualEqual" in title:
                remove.append(node)
            if "SetStaticMesh" in title:
                for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                    val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                    if val and "SM_4xScopeForSniper" in val:
                        remove.append(node)
            if "SetVisibility" in title:
                exec_in = node.find_input_pin("execute")
                if exec_in:
                    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(exec_in):
                        owner = lp.get_owning_node()
                        if owner in remove:
                            remove.append(node)

    remove = list({id(n): n for n in remove}.values())

    # reconnect spawn att directly to downstream if broken
    for spawn_name in SPAWN_ATT_NAMES:
        spawn_att = None
        for node in editor.list_all_nodes():
            if node.get_name() == spawn_name:
                spawn_att = node
                break
        if not spawn_att:
            continue
        then = spawn_att.find_output_pin("then")
        if not then:
            continue
        linked = list(unreal.BlueprintGraphPinLibrary.list_connected_pins(then))
        if linked and linked[0].get_owning_node() not in remove:
            continue
        # find Set ProceduralValues exec downstream from old chain
        downstream = None
        for node in editor.list_all_nodes():
            if node.get_class().get_name() != "K2Node_VariableSet":
                continue
            if "ProceduralValues" not in str(node.get_node_title()):
                continue
            exec_pin = node.find_input_pin("execute")
            if exec_pin and not unreal.BlueprintGraphPinLibrary.list_connected_pins(exec_pin):
                downstream = exec_pin
                break
        if downstream:
            connect_exec(then, downstream)
            log(f"Reconnected {spawn_name} -> Set ProceduralValues")

    if remove:
        editor.remove_nodes(remove)
        log(f"Removed {len(remove)} broken character scope node(s)")


def fix_hands_slot(char_bp) -> None:
    for graph in unreal.BlueprintEditorLibrary.list_graphs(char_bp):
        if graph.get_name() != "BeginSetup":
            continue
        editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        for node in editor.list_all_nodes():
            if node.get_name() != "K2Node_GenericCreateObject_2":
                continue
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                if pname.startswith("ItemData_Attachments"):
                    pin.set_pin_value(SNIPER_ATTACHMENTS)
            log("HandsSlot sight = SCOPE")
            return


def item_spawnattachments_wired(editor) -> bool:
    for node in editor.list_all_nodes():
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


def wire_item_spawnattachments(item_bp) -> None:
    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(item_bp)
    )
    if item_spawnattachments_wired(editor):
        log("Item SpawnAttachments already applies scope mesh")
        return

    spawn_event = None
    for node in editor.list_all_nodes():
        if node.get_class().get_name() != "K2Node_CustomEvent":
            continue
        if "SpawnAttachments" in str(node.get_node_title()):
            spawn_event = node
            break
    if not spawn_event:
        raise RuntimeError("Item SpawnAttachments event missing")

    branch = editor.add_branch_node()
    set_mesh = editor.add_call_function_node(SET_STATIC_MESH_FN)
    set_vis = editor.add_call_function_node(SET_VISIBILITY_FN)
    get_optic = editor.add_get_member_variable_node("OpticSight")
    get_optic_mesh = editor.add_get_member_variable_node("OpticSightMesh")
    is_valid = editor.add_call_function_node("/Script/Engine.KismetSystemLibrary:IsValid")
    if not all((branch, set_mesh, set_vis, get_optic, get_optic_mesh, is_valid)):
        raise RuntimeError("Failed creating item SpawnAttachments nodes")

    connect_data(output_pin(get_optic_mesh, "OpticSightMesh"), is_valid.find_input_pin("Object"))
    connect_data(output_pin(is_valid, "ReturnValue"), branch.find_input_pin("Condition"))
    connect_data(output_pin(get_optic, "OpticSight"), set_mesh.find_input_pin("self"))
    connect_data(output_pin(get_optic, "OpticSight"), set_vis.find_input_pin("self"))
    connect_data(output_pin(get_optic_mesh, "OpticSightMesh"), set_mesh.find_input_pin("NewMesh"))

    vis_pin = set_vis.find_input_pin("bNewVisibility")
    if vis_pin:
        vis_pin.set_pin_value("true")

    then_pin = spawn_event.find_output_pin("then")
    if not insert_exec_after(then_pin, branch, None):
        raise RuntimeError("Failed wiring item SpawnAttachments branch")
    connect_exec(branch.find_output_pin("then"), set_mesh.find_input_pin("execute"))
    connect_exec(set_mesh.find_output_pin("then"), set_vis.find_input_pin("execute"))
    log("Wired item SpawnAttachments -> OpticSightMesh -> OpticSight SetStaticMesh")


def wire_sniper_scope_paths(sniper_bp, scope_mesh) -> None:
    for graph_name in ("EventGraph", "UserConstructionScript"):
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
            if graph_name == "EventGraph" and "BeginPlay" in title:
                parent = node
            if graph_name == "UserConstructionScript" and "Construction Script" in title:
                parent = node

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
            set_mesh = editor.add_call_function_node(SET_STATIC_MESH_FN)
            get_optic = editor.add_get_member_variable_node("OpticSight")
            connect_data(output_pin(get_optic, "OpticSight"), set_mesh.find_input_pin("self"))
            insert_exec_after(parent.find_output_pin("then"), set_mesh, None)

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
        log(f"Sniper {graph_name} scope mesh chain refreshed")

    cdo = unreal.get_default_object(sniper_bp.generated_class())
    cdo.set_editor_property("ScopeSightMesh", scope_mesh)
    cdo.set_editor_property("OpticSightMesh", scope_mesh)

    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    for handle in sds.k2_gather_subobject_data_for_blueprint(sniper_bp):
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
        if not obj or "OpticSight" not in obj.get_name():
            continue
        if obj.get_class().get_name() != "StaticMeshComponent":
            continue
        obj.set_editor_property("static_mesh", scope_mesh)
        obj.set_editor_property("hidden_in_game", False)
    log("Updated sniper OpticSight template + mesh vars")


def tweak_sniper_recoil(sniper_bp) -> None:
    cdo = unreal.get_default_object(sniper_bp.generated_class())
    pv = cdo.get_editor_property("ProceduralValues")
    if not pv:
        return
    try:
        wv = pv.get_editor_property("WeaponValues")
        loc = wv.get_editor_property("BasePoseLoc")
        new_loc = unreal.Vector(float(loc.x), float(loc.y) * 0.82, float(loc.z) * 0.92)
        wv.set_editor_property("BasePoseLoc", new_loc)
        pv.set_editor_property("WeaponValues", wv)
        pv.modify()
        unreal.EditorAssetLibrary.save_asset(pv.get_path_name(), only_if_is_dirty=False)
        log(f"Reduced sniper BasePoseLoc kick")
    except Exception as exc:
        log(f"Recoil tweak skipped: {exc}")


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    char_bp = unreal.load_asset(f"{CHAR_BP}.BP_FPCharacter")
    item_bp = unreal.load_asset(f"{ITEM_BP}.BP_Item_Base")
    sniper_bp = unreal.load_asset(f"{SNIPER_BP}.BP_Weapon_Sniper")
    scope_mesh = unreal.load_asset(SCOPE_MESH)
    if not all((char_bp, item_bp, sniper_bp, scope_mesh)):
        raise RuntimeError("Missing assets")

    cleanup_character_scope_nodes(char_bp)
    fix_hands_slot(char_bp)
    unreal.BlueprintEditorLibrary.compile_blueprint(char_bp)
    unreal.EditorAssetLibrary.save_asset(CHAR_BP, only_if_is_dirty=False)

    wire_item_spawnattachments(item_bp)
    unreal.BlueprintEditorLibrary.compile_blueprint(item_bp)
    unreal.EditorAssetLibrary.save_asset(ITEM_BP, only_if_is_dirty=False)

    wire_sniper_scope_paths(sniper_bp, scope_mesh)
    tweak_sniper_recoil(sniper_bp)
    sniper_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(sniper_bp)
    unreal.EditorAssetLibrary.save_asset(SNIPER_BP, only_if_is_dirty=False)
    log("Done")


main()
