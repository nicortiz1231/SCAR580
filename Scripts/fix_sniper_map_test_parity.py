"""Match Map_Test sniper: pickup attachments + ScopeSightMesh on OpticSight, stock ADS."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_sniper_map_test_parity.log")
CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
SNIPER_BP = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper"
SCOPE_MESH = "/Game/BodycamFPSKIT/Demo/Meshes/SM_4xScopeForSniper.SM_4xScopeForSniper"
SET_STATIC_MESH_FN = "/Script/Engine.StaticMeshComponent:SetStaticMesh"
SET_VISIBILITY_FN = "/Script/Engine.SceneComponent:SetVisibility"

# BP_Weapon_Pickup_Sniper: HOLOSIGHT + laser + suppressor
PICKUP_ATTACHMENTS = (
    "(Sight_37_688233D743AA415C91250EBC240B11ED=NewEnumerator1,"
    "Laser_38_3209213B48BBF0256E8473A33CC4C0FE=NewEnumerator1,"
    "Muzzle_42_288332C341D7A8B7E31632867A1FE4DB=NewEnumerator1,"
    "Grip_46_62A21AB489496DC33D1ACDA661CA2D84=NewEnumerator0)"
)

SPAWN_CHAINS = (
    ("K2Node_CallFunction_140", "K2Node_VariableGet_133"),
    ("K2Node_CallFunction_141", "K2Node_VariableGet_83"),
)


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[map_test_parity] {msg}")


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


def insert_exec_after(exec_out_pin, new_node, downstream_exec_pin=None) -> bool:
    exec_in = new_node.find_input_pin("execute")
    exec_out = new_node.find_output_pin("then")
    if not exec_in or not exec_out:
        return False
    if downstream_exec_pin:
        exec_out_pin.break_pin_links()
        if not connect_exec(exec_out_pin, exec_in):
            return False
        return connect_exec(exec_out, downstream_exec_pin)
    if exec_out_pin:
        exec_out_pin.break_pin_links()
        return connect_exec(exec_out_pin, exec_in)
    return connect_exec(exec_out_pin, exec_in)


def exec_already_has_scope_chain(exec_in_pin) -> bool:
    if not exec_in_pin:
        return False
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(exec_in_pin):
        owner = lp.get_owning_node()
        if "SetStaticMesh" in str(owner.get_node_title()):
            return True
    return False


def wire_scope_from_variable(editor, exec_in_pin) -> None:
    """SetStaticMesh(OpticSight, ScopeSightMesh) -> SetVisibility(true)."""
    if exec_already_has_scope_chain(exec_in_pin):
        log("Exec pin already has scope SetStaticMesh chain")
        return

    set_mesh = editor.add_call_function_node(SET_STATIC_MESH_FN)
    set_vis = editor.add_call_function_node(SET_VISIBILITY_FN)
    get_optic = editor.add_get_member_variable_node("OpticSight")
    get_scope_mesh = editor.add_get_member_variable_node("ScopeSightMesh")
    if not all((set_mesh, set_vis, get_optic, get_scope_mesh)):
        raise RuntimeError("Failed creating scope apply nodes")

    connect_data(output_pin(get_optic, "OpticSight"), set_mesh.find_input_pin("self"))
    connect_data(output_pin(get_scope_mesh, "ScopeSightMesh"), set_mesh.find_input_pin("NewMesh"))
    connect_data(output_pin(get_optic, "OpticSight"), set_vis.find_input_pin("self"))
    vis_pin = set_vis.find_input_pin("bNewVisibility")
    if vis_pin:
        vis_pin.set_pin_value("true")

    if not insert_exec_after(exec_in_pin, set_mesh, set_vis.find_input_pin("execute")):
        raise RuntimeError("Failed wiring SetStaticMesh exec")
    connect_exec(set_mesh.find_output_pin("then"), set_vis.find_input_pin("execute"))
    log("Wired ScopeSightMesh -> OpticSight SetStaticMesh -> SetVisibility")


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
                if not pname.startswith("ItemData_Attachments"):
                    continue
                if not pin.set_pin_value(PICKUP_ATTACHMENTS):
                    raise RuntimeError("Failed setting HandsSlot attachments")
                after = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                log(f"HandsSlot attachments -> {after}")
                return
    raise RuntimeError("HandsSlot construct node not found")


def reconnect_spawn_chains(char_bp) -> None:
    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
    )
    for spawn_name, get_name in SPAWN_CHAINS:
        spawn_att = var_get = None
        for node in editor.list_all_nodes():
            if node.get_name() == spawn_name:
                spawn_att = node
            if node.get_name() == get_name:
                var_get = node
        if not spawn_att or not var_get:
            continue
        then = spawn_att.find_output_pin("then")
        exec_in = var_get.find_input_pin("execute")
        if not then or not exec_in:
            continue
        linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then)]
        if get_name in linked:
            log(f"{spawn_name} already connected")
            continue
        then.break_pin_links()
        connect_exec(then, exec_in)
        log(f"Reconnected {spawn_name} -> {get_name}")


def cleanup_misnamed_custom_events(editor) -> None:
    remove = []
    for node in editor.list_all_nodes():
        if node.get_class().get_name() != "K2Node_CustomEvent":
            continue
        title = str(node.get_node_title()).replace("\n", " ")
        if title.startswith("CustomEvent"):
            remove.append(node)
    if remove:
        editor.remove_nodes(remove)
        log(f"Removed {len(remove)} misnamed custom event node(s)")


def ensure_sniper_scope_paths(sniper_bp) -> None:
    scope_mesh = unreal.load_asset(SCOPE_MESH)
    cdo = unreal.get_default_object(sniper_bp.generated_class())
    cdo.set_editor_property("ScopeSightMesh", scope_mesh)
    # Keep stock OpticSightMesh (SM_SightSniper) — do not overwrite.

    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    seen = set()
    for handle in sds.k2_gather_subobject_data_for_blueprint(sniper_bp):
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(
            unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        )
        if not obj or "OpticSight" not in obj.get_name() or obj.get_class().get_name() != "StaticMeshComponent":
            continue
        if id(obj) in seen:
            continue
        seen.add(id(obj))
        obj.set_editor_property("static_mesh", scope_mesh)
        obj.set_editor_property("hidden_in_game", False)
    log("OpticSight template + ScopeSightMesh CDO set")

    event_graph = unreal.BlueprintEditorLibrary.find_event_graph(sniper_bp)
    eg = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)
    cleanup_misnamed_custom_events(eg)

    parent_begin = None
    for node in eg.list_all_nodes():
        if node.get_class().get_name() == "K2Node_CallParentFunction" and "BeginPlay" in str(node.get_node_title()):
            parent_begin = node
            break
    if parent_begin:
        wire_scope_from_variable(eg, parent_begin.find_output_pin("then"))
    log("Scope applied on BeginPlay (stock Map_Test uses ScopeSightMesh on OpticSight)")


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    char_bp = unreal.load_asset(f"{CHAR_BP}.BP_FPCharacter")
    sniper_bp = unreal.load_asset(f"{SNIPER_BP}.BP_Weapon_Sniper")
    if not char_bp or not sniper_bp:
        raise RuntimeError("Missing blueprints")

    fix_hands_slot(char_bp)
    reconnect_spawn_chains(char_bp)
    char_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(char_bp)
    unreal.EditorAssetLibrary.save_asset(CHAR_BP, only_if_is_dirty=False)
    # Re-apply attachments after compile (pin defaults can reset during compile)
    fix_hands_slot(char_bp)
    char_bp.modify()
    unreal.EditorAssetLibrary.save_asset(CHAR_BP, only_if_is_dirty=False)

    ensure_sniper_scope_paths(sniper_bp)
    sniper_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(sniper_bp)
    unreal.EditorAssetLibrary.save_asset(SNIPER_BP, only_if_is_dirty=False)

    cdo = unreal.get_default_object(sniper_bp.generated_class())
    log(
        f"Verify AimDistance={cdo.get_editor_property('AimDistanceFromCamera')} "
        f"Scope={cdo.get_editor_property('ScopeSightMesh').get_name()} "
        f"Optic={cdo.get_editor_property('OpticSightMesh').get_name()}"
    )
    log("Done")


main()
