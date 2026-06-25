"""Use the sniper 4x scope mesh instead of the holo/red-dot sight."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_sniper_correct_scope.log")

SNIPER_BP = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper"
CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
SCOPE_MESH = "/Game/BodycamFPSKIT/Demo/Meshes/SM_4xScopeForSniper.SM_4xScopeForSniper"
SET_STATIC_MESH_FN = "/Script/Engine.StaticMeshComponent:SetStaticMesh"
# SCOPE enum entry (EMPTY=0, HOLOSIGHT=1, SCOPE=2)
SNIPER_ATTACHMENTS = (
    "(Sight_37_688233D743AA415C91250EBC240B11ED=NewEnumerator2,"
    "Laser_38_3209213B48BBF0256E8473A33CC4C0FE=NewEnumerator0,"
    "Muzzle_42_288332C341D7A8B7E31632867A1FE4DB=NewEnumerator0,"
    "Grip_46_62A21AB489496DC33D1ACDA661CA2D84=NewEnumerator5)"
)


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[fix_sniper_scope] {msg}")


def connect_exec(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def connect_data(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def set_pin_value_by_prefix(node, prefix: str, value: str) -> None:
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        if pname.startswith(prefix):
            if not pin.set_pin_value(value):
                raise RuntimeError(f"Failed setting {pname}={value!r}")


def fix_hands_slot_loadout(char_bp) -> None:
    begin_graph = None
    for graph in unreal.BlueprintEditorLibrary.list_graphs(char_bp):
        if graph.get_name() == "BeginSetup":
            begin_graph = graph
            break
    if not begin_graph:
        raise RuntimeError("BeginSetup graph missing")

    editor = unreal.BlueprintGraphEditor.get_graph_editor(begin_graph)
    for node in editor.list_all_nodes():
        if node.get_name() != "K2Node_GenericCreateObject_2":
            continue
        set_pin_value_by_prefix(node, "ItemData_Attachments", SNIPER_ATTACHMENTS)
        set_pin_value_by_prefix(node, "ItemData_AmmoCount", "12")
        set_pin_value_by_prefix(node, "ItemData_MaxAmmo", "120")
        log("HandsSlot sight -> NewEnumerator2 (SCOPE)")
        return
    raise RuntimeError("HandsSlot construct node missing")


def cleanup_sniper_beginplay_scope(sniper_bp) -> None:
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

    # Remove duplicate scope SetStaticMesh nodes; keep one canonical node.
    scope_nodes = []
    for node in editor.list_all_nodes():
        if node.get_class().get_name() != "K2Node_CallFunction":
            continue
        if "SetStaticMesh" not in str(node.get_node_title()):
            continue
        self_pin = node.find_input_pin("self")
        if not self_pin:
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(self_pin):
            owner = lp.get_owning_node()
            if owner.get_class().get_name() == "K2Node_VariableGet":
                if "OpticSight" in str(owner.get_node_title()):
                    scope_nodes.append(node)

    keep = scope_nodes[0] if scope_nodes else None
    remove = scope_nodes[1:]
    if remove:
        editor.remove_nodes(remove)
        log(f"Removed {len(remove)} duplicate sniper SetStaticMesh node(s)")

    if not keep:
        keep = editor.add_call_function_node(SET_STATIC_MESH_FN)
        if not keep:
            raise RuntimeError("Failed to create SetStaticMesh node")
        get_optic = editor.add_get_member_variable_node("OpticSight")
        optic_out = None
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(get_optic):
            if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) == unreal.EdGraphPinDirection.EGPD_OUTPUT:
                optic_out = pin
                break
        connect_data(optic_out, keep.find_input_pin("self"))

    # Hard-pin the 4x sniper scope asset so holo OpticSightMesh can never win.
    new_mesh_pin = keep.find_input_pin("NewMesh")
    if new_mesh_pin:
        new_mesh_pin.set_pin_value(SCOPE_MESH)
        log(f"SetStaticMesh NewMesh pin -> {SCOPE_MESH}")

    # Exec: BeginPlay -> Parent BeginPlay -> SetStaticMesh
    begin_then = begin.find_then_pin()
    parent_exec = parent_begin.find_input_pin("execute")
    parent_then = parent_begin.find_then_pin()
    keep_exec = keep.find_input_pin("execute")
    if begin_then and parent_exec:
        begin_then.break_pin_links()
        connect_exec(begin_then, parent_exec)
    if parent_then and keep_exec:
        parent_then.break_pin_links()
        connect_exec(parent_then, keep_exec)

    log("Sniper BeginPlay applies SM_4xScopeForSniper to OpticSight")


def fix_sniper_cdo_meshes(sniper_bp) -> None:
    scope_mesh = unreal.load_asset(SCOPE_MESH)
    cdo = unreal.get_default_object(sniper_bp.generated_class())

    cdo.set_editor_property("ScopeSightMesh", scope_mesh)
    cdo.set_editor_property("OpticSightMesh", scope_mesh)
    log("CDO ScopeSightMesh and OpticSightMesh -> SM_4xScopeForSniper")

    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    seen = set()
    changed = 0
    for handle in sds.k2_gather_subobject_data_for_blueprint(sniper_bp):
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
        if not obj or "OpticSight" not in obj.get_name():
            continue
        if obj.get_class().get_name() != "StaticMeshComponent":
            continue
        obj_id = id(obj)
        if obj_id in seen:
            continue
        seen.add(obj_id)
        obj.set_editor_property("static_mesh", scope_mesh)
        changed += 1
    log(f"OpticSight component template static_mesh set on {changed} component(s)")


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    char_bp = unreal.load_asset(f"{CHAR_BP}.BP_FPCharacter")
    sniper_bp = unreal.load_asset(f"{SNIPER_BP}.BP_Weapon_Sniper")
    if not char_bp or not sniper_bp:
        raise RuntimeError("Missing character or sniper blueprint")

    fix_hands_slot_loadout(char_bp)
    unreal.BlueprintEditorLibrary.compile_blueprint(char_bp)
    unreal.EditorAssetLibrary.save_asset(CHAR_BP, only_if_is_dirty=False)

    cleanup_sniper_beginplay_scope(sniper_bp)
    fix_sniper_cdo_meshes(sniper_bp)
    sniper_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(sniper_bp)
    unreal.EditorAssetLibrary.save_asset(SNIPER_BP, only_if_is_dirty=False)
    log("Done")


main()
