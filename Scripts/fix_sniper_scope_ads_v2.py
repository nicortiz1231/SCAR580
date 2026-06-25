"""Fix sniper missing scope mesh and ADS mesh clipping."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_sniper_scope_ads_v2.log")

SNIPER_BP = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper"
CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
ITEM_BP = "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base"
SCOPE_MESH = "/Game/BodycamFPSKIT/Demo/Meshes/SM_4xScopeForSniper.SM_4xScopeForSniper"
SET_STATIC_MESH_FN = "/Script/Engine.StaticMeshComponent:SetStaticMesh"
SPAWN_ATTACHMENTS_FN = f"{ITEM_BP}.BP_Item_Base_C:SpawnAttachments"
SNIPER_ATTACHMENTS = (
    "(Sight_37_688233D743AA415C91250EBC240B11ED=NewEnumerator4,"
    "Laser_38_3209213B48BBF0256E8473A33CC4C0FE=NewEnumerator4,"
    "Muzzle_42_288332C341D7A8B7E31632867A1FE4DB=NewEnumerator4,"
    "Grip_46_62A21AB489496DC33D1ACDA661CA2D84=NewEnumerator5)"
)
AIM_DISTANCE = 22.0
MARKER = "Sniper Scope Fix v2"


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[fix_sniper_v2] {msg}")


def connect_exec(src, dst) -> bool:
    if src and dst:
        return bool(src.try_create_connection(dst))
    return False


def connect_data(src, dst) -> bool:
    if src and dst:
        return bool(src.try_create_connection(dst))
    return False


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


def set_pin_value_by_prefix(node, prefix: str, value: str) -> bool:
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        if pname.startswith(prefix):
            if not pin.set_pin_value(value):
                raise RuntimeError(f"Failed setting {pname}={value!r}")
            return True
    return False


def fix_hands_slot_loadout(char_bp) -> None:
    begin_graph = None
    for graph in unreal.BlueprintEditorLibrary.list_graphs(char_bp):
        if graph.get_name() == "BeginSetup":
            begin_graph = graph
            break
    if not begin_graph:
        raise RuntimeError("BeginSetup graph missing")

    editor = unreal.BlueprintGraphEditor.get_graph_editor(begin_graph)
    construct = None
    for node in editor.list_all_nodes():
        if node.get_name() == "K2Node_GenericCreateObject_2":
            construct = node
            break
    if not construct:
        raise RuntimeError("HandsSlot construct node missing")

    set_pin_value_by_prefix(construct, "ItemData_Attachments", SNIPER_ATTACHMENTS)
    set_pin_value_by_prefix(construct, "ItemData_AmmoCount", "12")
    set_pin_value_by_prefix(construct, "ItemData_MaxAmmo", "120")
    log("Updated HandsSlot construct to scoped sniper loadout")


def fix_fallback_ammo(char_bp) -> None:
    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
    )
    for node in editor.list_all_nodes():
        if node.get_name() != "K2Node_CallFunction_212":
            continue
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if pname == "AmmoCount":
                pin.set_pin_value("12")
            elif pname == "MaxAmmo":
                pin.set_pin_value("120")
        log("Updated fallback sniper SetAmmo to 12/120")


def spawn_attachments_already_wired(editor, setammo_name: str) -> bool:
    for node in editor.list_all_nodes():
        if node.get_name() != setammo_name:
            continue
        then_pin = node.find_then_pin()
        if not then_pin:
            return False
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then_pin):
            owner = lp.get_owning_node()
            if "SpawnAttachments" in str(owner.get_node_title()):
                return True
    return False


def find_spawned_item_get(editor):
    for node in editor.list_all_nodes():
        if node.get_class().get_name() != "K2Node_VariableGet":
            continue
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            if str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin)) != "SpawnedItem":
                continue
            if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) != unreal.EdGraphPinDirection.EGPD_OUTPUT:
                continue
            return node
    return None


def find_downstream_exec_pin(editor, setammo_node, fallback_exec_node_name: str | None = None):
    then_pin = setammo_node.find_then_pin()
    if then_pin:
        for linked in unreal.BlueprintGraphPinLibrary.list_connected_pins(then_pin):
            if linked.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT:
                return linked

    if not fallback_exec_node_name:
        return None

    for node in editor.list_all_nodes():
        if node.get_name() != fallback_exec_node_name:
            continue
        exec_pin = node.find_input_pin("execute")
        if exec_pin:
            return exec_pin
    return None


def insert_spawn_attachments_after_setammo(char_bp) -> None:
    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
    )
    spawned_item_get = find_spawned_item_get(editor)
    if not spawned_item_get:
        log("SpawnedItem variable get not found; skipping SpawnAttachments wiring")
        return

    setammo_fallback_exec = {
        "K2Node_CallFunction_212": "K2Node_VariableGet_83",
        "K2Node_CallFunction_234": "K2Node_VariableGet_133",
    }

    for setammo_name in ("K2Node_CallFunction_212", "K2Node_CallFunction_234"):
        if spawn_attachments_already_wired(editor, setammo_name):
            log(f"{setammo_name} already wired to SpawnAttachments")
            continue

        setammo = None
        for node in editor.list_all_nodes():
            if node.get_name() == setammo_name:
                setammo = node
                break
        if not setammo:
            continue

        then_pin = setammo.find_then_pin()
        if not then_pin:
            continue

        downstream = find_downstream_exec_pin(
            editor, setammo, setammo_fallback_exec.get(setammo_name)
        )
        if not downstream:
            log(f"No downstream exec pin for {setammo_name}")
            continue

        spawn_att = editor.add_call_function_node(SPAWN_ATTACHMENTS_FN)
        if not spawn_att:
            log(f"Could not create SpawnAttachments node for {setammo_name}")
            continue

        exec_in = spawn_att.find_input_pin("execute")
        exec_out = spawn_att.find_output_pin("then")
        self_pin = spawn_att.find_input_pin("self")
        spawned_out = spawned_item_get.find_output_pin("SpawnedItem")
        if not (exec_in and exec_out and self_pin and spawned_out):
            editor.remove_nodes([spawn_att])
            log(f"SpawnAttachments node missing pins for {setammo_name}")
            continue

        then_pin.break_pin_links()
        connect_exec(then_pin, exec_in)
        connect_data(spawned_out, self_pin)
        connect_exec(exec_out, downstream)
        log(f"Wired {setammo_name} -> SpawnAttachments -> downstream")


def sniper_beginplay_scope_wired(editor) -> bool:
    parent_begin = None
    for node in editor.list_all_nodes():
        if node.get_class().get_name() == "K2Node_CallParentFunction":
            if "BeginPlay" in str(node.get_node_title()):
                parent_begin = node
                break
    if not parent_begin:
        return False

    then_pin = parent_begin.find_then_pin()
    if not then_pin:
        return False

    for linked in unreal.BlueprintGraphPinLibrary.list_connected_pins(then_pin):
        owner = linked.get_owning_node()
        if owner.get_class().get_name() == "K2Node_CallFunction":
            if "SetStaticMesh" in str(owner.get_node_title()):
                return True
    return False


def wire_sniper_beginplay_scope(sniper_bp) -> None:
    event_graph = unreal.BlueprintEditorLibrary.find_event_graph(sniper_bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)
    if sniper_beginplay_scope_wired(editor):
        log("Sniper BeginPlay scope wiring already present")
        return

    parent_begin = None
    for node in editor.list_all_nodes():
        if node.get_class().get_name() == "K2Node_CallParentFunction":
            if "BeginPlay" in str(node.get_node_title()):
                parent_begin = node
                break
    if not parent_begin:
        raise RuntimeError("Sniper missing Parent BeginPlay node")

    set_mesh = editor.add_call_function_node(SET_STATIC_MESH_FN)
    get_optic = editor.add_get_member_variable_node("OpticSight")
    get_scope_mesh = editor.add_get_member_variable_node("ScopeSightMesh")
    if not (set_mesh and get_optic and get_scope_mesh):
        raise RuntimeError("Failed to create sniper scope BeginPlay nodes")

    if not insert_exec_after_pin(parent_begin.find_then_pin(), set_mesh):
        raise RuntimeError("Failed to wire sniper BeginPlay exec chain")

    optic_out = get_optic.find_output_pin("OpticSight")
    if not optic_out:
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(get_optic):
            if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) == unreal.EdGraphPinDirection.EGPD_OUTPUT:
                optic_out = pin
                break

    mesh_out = get_scope_mesh.find_output_pin("ScopeSightMesh")
    if not mesh_out:
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(get_scope_mesh):
            if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) == unreal.EdGraphPinDirection.EGPD_OUTPUT:
                mesh_out = pin
                break

    self_pin = set_mesh.find_input_pin("self")
    new_mesh_pin = set_mesh.find_input_pin("NewMesh")
    if not (optic_out and mesh_out and self_pin and new_mesh_pin):
        raise RuntimeError("Missing SetStaticMesh pin wiring targets")

    connect_data(optic_out, self_pin)
    connect_data(mesh_out, new_mesh_pin)

    comment = editor.add_comment_node(MARKER, unreal.Vector2D(0, 0))
    if comment:
        try:
            comment.set_editor_property("node_comment", MARKER)
        except Exception:
            pass

    log("Wired sniper BeginPlay to SetStaticMesh(OpticSight, ScopeSightMesh)")


def fix_optic_component_template(sniper_bp) -> None:
    scope_mesh = unreal.load_asset(SCOPE_MESH)
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    seen = set()
    changed = 0
    for handle in sds.k2_gather_subobject_data_for_blueprint(sniper_bp):
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
        if not obj or "OpticSight" not in obj.get_name():
            continue
        obj_id = id(obj)
        if obj_id in seen:
            continue
        seen.add(obj_id)
        if obj.get_class().get_name() != "StaticMeshComponent":
            continue
        obj.set_editor_property("static_mesh", scope_mesh)
        changed += 1
    log(f"Set OpticSight template static_mesh on {changed} unique component(s)")


def fix_aim_distance(sniper_bp) -> None:
    cdo = unreal.get_default_object(sniper_bp.generated_class())
    aim = float(cdo.get_editor_property("AimDistanceFromCamera"))
    if aim < AIM_DISTANCE - 0.1:
        cdo.set_editor_property("AimDistanceFromCamera", AIM_DISTANCE)
        log(f"AimDistanceFromCamera {aim} -> {AIM_DISTANCE}")
    else:
        log(f"AimDistanceFromCamera already {aim}")


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    char_bp = unreal.load_asset(f"{CHAR_BP}.BP_FPCharacter")
    sniper_bp = unreal.load_asset(f"{SNIPER_BP}.BP_Weapon_Sniper")
    if not char_bp or not sniper_bp:
        raise RuntimeError("Missing character or sniper blueprint")

    fix_hands_slot_loadout(char_bp)
    fix_fallback_ammo(char_bp)
    insert_spawn_attachments_after_setammo(char_bp)
    unreal.BlueprintEditorLibrary.compile_blueprint(char_bp)
    unreal.EditorAssetLibrary.save_asset(CHAR_BP, only_if_is_dirty=False)

    wire_sniper_beginplay_scope(sniper_bp)
    fix_optic_component_template(sniper_bp)
    fix_aim_distance(sniper_bp)
    sniper_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(sniper_bp)
    unreal.EditorAssetLibrary.save_asset(SNIPER_BP, only_if_is_dirty=False)
    log("Done")


main()
