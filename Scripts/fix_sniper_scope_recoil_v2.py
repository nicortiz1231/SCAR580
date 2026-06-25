"""Ensure sniper 4x scope appears and reduce recoil near-plane clipping."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_sniper_scope_recoil_v2.log")

CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
SNIPER_BP = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper"
SCOPE_MESH = "/Game/BodycamFPSKIT/Demo/Meshes/SM_4xScopeForSniper.SM_4xScopeForSniper"
SET_STATIC_MESH_FN = "/Script/Engine.StaticMeshComponent:SetStaticMesh"
SET_VISIBILITY_FN = "/Script/Engine.SceneComponent:SetVisibility"
ITEM_CLASS = "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base_C"
SNIPER_CLASS = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper_C"
EQUAL_OBJECT_FN = "/Script/Engine.KismetMathLibrary:EqualEqual_ObjectObject"
SNIPER_ATTACHMENTS = (
    "(Sight_37_688233D743AA415C91250EBC240B11ED=NewEnumerator2,"
    "Laser_38_3209213B48BBF0256E8473A33CC4C0FE=NewEnumerator0,"
    "Muzzle_42_288332C341D7A8B7E31632867A1FE4DB=NewEnumerator0,"
    "Grip_46_62A21AB489496DC33D1ACDA661CA2D84=NewEnumerator5)"
)
SPAWN_ATT_NODES = ("K2Node_CallFunction_140", "K2Node_CallFunction_141")
SPAWNED_ITEM_GET = {
    "K2Node_CallFunction_140": "K2Node_VariableGet_133",
    "K2Node_CallFunction_141": "K2Node_VariableGet_83",
}
NEAR_CLIP = 2.5


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[fix_sniper_v2] {msg}")


def connect_target(node, spawned_out) -> None:
    for pin_name in ("self", "Target"):
        pin = node.find_input_pin(pin_name)
        if pin:
            connect_data(spawned_out, pin)
            return
    raise RuntimeError(f"No self/Target pin on {node.get_name()}")


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


def insert_exec_between(exec_out_pin, new_node, downstream_exec_pin) -> bool:
    exec_in = new_node.find_input_pin("execute")
    exec_out = new_node.find_output_pin("then")
    if not exec_in or not exec_out:
        return False
    if downstream_exec_pin:
        exec_out_pin.break_pin_links()
        if not connect_exec(exec_out_pin, exec_in):
            return False
        return connect_exec(exec_out, downstream_exec_pin)
    return connect_exec(exec_out_pin, exec_in)


def wire_scope_apply_nodes(editor, exec_in_pin):
    """Exec: SetStaticMesh(SM_4xScopeForSniper) -> SetVisibility(true)."""
    set_mesh = editor.add_call_function_node(SET_STATIC_MESH_FN)
    set_vis = editor.add_call_function_node(SET_VISIBILITY_FN)
    get_optic = editor.add_get_member_variable_node("OpticSight")
    if not (set_mesh and set_vis and get_optic):
        raise RuntimeError("Failed creating scope apply nodes")

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

    if not insert_exec_between(exec_in_pin, set_mesh, None):
        raise RuntimeError("Failed wiring scope SetStaticMesh exec")
    connect_exec(set_mesh.find_output_pin("then"), set_vis.find_input_pin("execute"))
    return set_vis.find_output_pin("then")


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
            log("HandsSlot sight = NewEnumerator2 (SCOPE)")
            return


def scope_apply_already_after_spawnatt(editor, spawn_att_name: str) -> bool:
    node = None
    for n in editor.list_all_nodes():
        if n.get_name() == spawn_att_name:
            node = n
            break
    if not node:
        return False
    then = node.find_output_pin("then")
    if not then:
        return False
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
        owner = lp.get_owning_node()
        if owner.get_class().get_name() != "K2Node_IfThenElse":
            continue
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(owner):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if pname != "Condition":
                continue
            for lp2 in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                eq = lp2.get_owning_node()
                if "EqualEqual" not in str(eq.get_node_title()):
                    continue
                for pin2 in unreal.BlueprintEditorLibrary.list_all_pins(eq):
                    val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin2)
                    if val and "SM_4xScopeForSniper" in val:
                        return True
    return False


def repair_character_scope_targets(char_bp) -> None:
    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
    )
    for spawn_name, spawned_get_name in SPAWNED_ITEM_GET.items():
        spawned_get = None
        for node in editor.list_all_nodes():
            if node.get_name() == spawned_get_name:
                spawned_get = node
                break
        if not spawned_get:
            continue
        spawned_out = spawned_get.find_output_pin("SpawnedItem")
        if not spawned_out:
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(spawned_get):
                if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) == unreal.EdGraphPinDirection.EGPD_OUTPUT:
                    spawned_out = pin
                    break
        if not spawned_out:
            continue

        spawn_att = None
        for node in editor.list_all_nodes():
            if node.get_name() == spawn_name:
                spawn_att = node
                break
        if not spawn_att:
            continue

        then = spawn_att.find_output_pin("then")
        visited = set()
        stack = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
            stack.append(lp.get_owning_node())
        while stack:
            node = stack.pop()
            if id(node) in visited:
                continue
            visited.add(id(node))
            title = str(node.get_node_title())
            if node.get_class().get_name() == "K2Node_VariableGet":
                if "ScopeSightMesh" in title or "OpticSight" in title:
                    connect_target(node, spawned_out)
                    log(f"Repaired Target for {node.get_name()} on {spawn_name}")
            then_pin = node.find_output_pin("then")
            if then_pin:
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then_pin):
                    stack.append(lp.get_owning_node())


def insert_character_scope_apply(char_bp) -> None:
    """After SpawnAttachments, apply the sniper 4x scope mesh to the spawned weapon."""
    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
    )

    for spawn_name in SPAWN_ATT_NODES:
        if scope_apply_already_after_spawnatt(editor, spawn_name):
            log(f"{spawn_name} already followed by sniper scope apply")
            continue

        spawn_att = None
        for node in editor.list_all_nodes():
            if node.get_name() == spawn_name:
                spawn_att = node
                break
        if not spawn_att:
            log(f"Missing {spawn_name}")
            continue

        spawned_get_name = SPAWNED_ITEM_GET[spawn_name]
        spawned_get = None
        for node in editor.list_all_nodes():
            if node.get_name() == spawned_get_name:
                spawned_get = node
                break
        if not spawned_get:
            log(f"Missing spawned item get {spawned_get_name}")
            continue

        then_pin = spawn_att.find_output_pin("then")
        downstream = None
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then_pin):
            if lp.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT:
                downstream = lp
                break

        spawned_out = spawned_get.find_output_pin("SpawnedItem")
        if not spawned_out:
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(spawned_get):
                if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) == unreal.EdGraphPinDirection.EGPD_OUTPUT:
                    spawned_out = pin
                    break

        set_mesh = editor.add_call_function_node(SET_STATIC_MESH_FN)
        set_vis = editor.add_call_function_node(SET_VISIBILITY_FN)
        get_optic = editor.add_get_member_variable_node("OpticSight", ITEM_CLASS)
        get_scope_mesh = editor.add_get_member_variable_node("ScopeSightMesh", SNIPER_CLASS)
        equal = editor.add_call_function_node(EQUAL_OBJECT_FN)
        branch = editor.add_branch_node()
        if not all((set_mesh, set_vis, get_optic, get_scope_mesh, equal, branch)):
            raise RuntimeError(f"Failed creating character scope nodes for {spawn_name}")

        connect_target(get_optic, spawned_out)
        connect_target(get_scope_mesh, spawned_out)
        connect_data(output_pin(get_scope_mesh, "ScopeSightMesh"), equal.find_input_pin("A"))
        b_pin = equal.find_input_pin("B")
        if b_pin:
            b_pin.set_pin_value(SCOPE_MESH)
        connect_data(output_pin(equal, "ReturnValue"), branch.find_input_pin("Condition"))

        optic_out = output_pin(get_optic, "OpticSight")
        connect_data(optic_out, set_mesh.find_input_pin("self"))
        connect_data(optic_out, set_vis.find_input_pin("self"))

        mesh_pin = set_mesh.find_input_pin("NewMesh")
        if mesh_pin:
            mesh_pin.set_pin_value(SCOPE_MESH)
        vis_pin = set_vis.find_input_pin("bNewVisibility")
        if vis_pin:
            vis_pin.set_pin_value("true")

        if not insert_exec_between(then_pin, branch, None):
            raise RuntimeError(f"Failed wiring scope branch exec for {spawn_name}")
        connect_exec(branch.find_output_pin("then"), set_mesh.find_input_pin("execute"))
        connect_exec(set_mesh.find_output_pin("then"), set_vis.find_input_pin("execute"))
        connect_exec(set_vis.find_output_pin("then"), downstream)
        connect_exec(branch.find_output_pin("else"), downstream)
        log(f"Wired {spawn_name} -> sniper scope branch -> SetStaticMesh -> downstream")


def set_optic_scs_mesh(sniper_bp, scope_mesh) -> None:
    scs = None
    for prop in ("simple_construction_script", "SimpleConstructionScript"):
        try:
            scs = sniper_bp.get_editor_property(prop)
            if scs:
                break
        except Exception:
            pass
    if not scs:
        log("No simple_construction_script on sniper BP")
        return

    changed = 0
    try:
        nodes = scs.get_all_nodes()
    except Exception as exc:
        log(f"SCS get_all_nodes failed: {exc}")
        return

    for node in nodes:
        try:
            name = str(node.get_variable_name())
        except Exception:
            name = ""
        if "OpticSight" not in name:
            continue
        comp = node.component_template
        if not comp:
            continue
        comp.set_editor_property("static_mesh", scope_mesh)
        comp.set_editor_property("hidden_in_game", False)
        changed += 1
        log(f"SCS {name} static_mesh -> SM_4xScopeForSniper")

    if not changed:
        log("No OpticSight SCS node updated")


def fix_sniper_beginplay_and_ucs(sniper_bp) -> None:
    scope_mesh = unreal.load_asset(SCOPE_MESH)

    for graph_name in ("EventGraph", "UserConstructionScript"):
        graph = None
        for g in unreal.BlueprintEditorLibrary.list_graphs(sniper_bp):
            if g.get_name() == graph_name:
                graph = g
                break
        if not graph:
            continue
        editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)

        parent_node = None
        for node in editor.list_all_nodes():
            if node.get_class().get_name() != "K2Node_CallParentFunction":
                continue
            title = str(node.get_node_title())
            if graph_name == "EventGraph" and "BeginPlay" in title:
                parent_node = node
                break
            if graph_name == "UserConstructionScript" and "Construction Script" in title:
                parent_node = node
                break

        set_mesh = None
        set_vis = None
        for node in editor.list_all_nodes():
            if node.get_class().get_name() != "K2Node_CallFunction":
                continue
            title = str(node.get_node_title())
            if "SetStaticMesh" in title and set_mesh is None:
                set_mesh = node
            if "SetVisibility" in title and set_vis is None:
                set_vis = node

        if not set_mesh:
            parent_then = parent_node.find_output_pin("then") if parent_node else None
            wire_scope_apply_nodes(editor, parent_then)
            log(f"Created scope apply chain in sniper {graph_name}")
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

        parent_then = parent_node.find_output_pin("then") if parent_node else None
        if parent_then:
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(parent_then):
                if lp.get_owning_node() == set_mesh:
                    break
            else:
                parent_then.break_pin_links()
                connect_exec(parent_then, set_mesh.find_input_pin("execute"))

        mesh_then = set_mesh.find_output_pin("then")
        vis_exec = set_vis.find_input_pin("execute")
        if mesh_then and vis_exec:
            mesh_then.break_pin_links()
            connect_exec(mesh_then, vis_exec)
        log(f"Refreshed sniper {graph_name} scope mesh + visibility chain")

    cdo = unreal.get_default_object(sniper_bp.generated_class())
    cdo.set_editor_property("ScopeSightMesh", scope_mesh)
    cdo.set_editor_property("OpticSightMesh", scope_mesh)


def remove_misnamed_custom_event(sniper_bp) -> None:
    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(sniper_bp)
    )
    remove = []
    for node in editor.list_all_nodes():
        if node.get_class().get_name() != "K2Node_CustomEvent":
            continue
        if str(node.get_node_title()) == "CustomEvent":
            remove.append(node)
    if remove:
        editor.remove_nodes(remove)
        log(f"Removed {len(remove)} misnamed CustomEvent node(s) from sniper")


def tweak_sniper_weapon_pose_recoil(sniper_bp) -> None:
    """Slightly reduce backward base pose kick in sniper procedural values."""
    cdo = unreal.get_default_object(sniper_bp.generated_class())
    pv = cdo.get_editor_property("ProceduralValues")
    if not pv:
        return
    try:
        wv = pv.get_editor_property("WeaponValues")
        loc = wv.get_editor_property("BasePoseLoc")
        x, y, z = float(loc.x), float(loc.y), float(loc.z)
        # Pull weapon slightly away from camera on recoil-heavy axes.
        new_loc = unreal.Vector(x, y * 0.82, z * 0.92)
        wv.set_editor_property("BasePoseLoc", new_loc)
        pv.set_editor_property("WeaponValues", wv)
        pv.modify()
        unreal.EditorAssetLibrary.save_asset(pv.get_path_name(), only_if_is_dirty=False)
        log(f"Reduced sniper BasePoseLoc ({x},{y},{z}) -> ({new_loc.x},{new_loc.y},{new_loc.z})")
    except Exception as exc:
        log(f"Could not tweak sniper WeaponValues: {exc}")


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    char_bp = unreal.load_asset(f"{CHAR_BP}.BP_FPCharacter")
    sniper_bp = unreal.load_asset(f"{SNIPER_BP}.BP_Weapon_Sniper")
    scope_mesh = unreal.load_asset(SCOPE_MESH)
    if not char_bp or not sniper_bp or not scope_mesh:
        raise RuntimeError("Missing required assets")

    fix_hands_slot(char_bp)
    repair_character_scope_targets(char_bp)
    insert_character_scope_apply(char_bp)
    unreal.BlueprintEditorLibrary.compile_blueprint(char_bp)
    unreal.EditorAssetLibrary.save_asset(CHAR_BP, only_if_is_dirty=False)

    remove_misnamed_custom_event(sniper_bp)
    fix_sniper_beginplay_and_ucs(sniper_bp)
    set_optic_scs_mesh(sniper_bp, scope_mesh)
    tweak_sniper_weapon_pose_recoil(sniper_bp)
    sniper_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(sniper_bp)
    unreal.EditorAssetLibrary.save_asset(SNIPER_BP, only_if_is_dirty=False)
    log("Done")


main()
