"""Fix sniper missing scope mesh and ADS clipping for wheel-equipped sniper."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_sniper_scope_ads.log")

SNIPER_BP = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper"
CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
SCOPE_MESH = "/Game/BodycamFPSKIT/Demo/Meshes/SM_4xScopeForSniper.SM_4xScopeForSniper"
SNIPER_ATTACHMENTS = (
    "(Sight_37_688233D743AA415C91250EBC240B11ED=NewEnumerator4,"
    "Laser_38_3209213B48BBF0256E8473A33CC4C0FE=NewEnumerator4,"
    "Muzzle_42_288332C341D7A8B7E31632867A1FE4DB=NewEnumerator4,"
    "Grip_46_62A21AB489496DC33D1ACDA661CA2D84=NewEnumerator0)"
)


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[fix_sniper] {msg}")


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
    log("Updated HandsSlot construct to sniper pickup loadout")


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


def insert_spawn_attachments_after_setammo(char_bp) -> None:
    """Call SpawnAttachments on the spawned weapon after both swap SetAmmo nodes."""
    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
    )

    template = None
    spawned_item_get = None
    for node in editor.list_all_nodes():
        if node.get_name() == "K2Node_CallFunction_46":
            template = node
        if node.get_name() == "K2Node_VariableGet_20":
            spawned_item_get = node

    if not template or not spawned_item_get:
        log("SpawnAttachments template nodes not found; skipping exec wiring")
        return

    def already_wired(setammo_name: str) -> bool:
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

    for setammo_name in ("K2Node_CallFunction_212", "K2Node_CallFunction_234"):
        if already_wired(setammo_name):
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

        downstream = None
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then_pin):
            downstream = lp
            break
        if not downstream:
            continue

        unreal.BlueprintGraphPinLibrary.break_pin_links(then_pin)

        new_node = editor.duplicate_node(template, template.get_node_pos())
        if not new_node:
            # restore link if duplicate fails
            then_pin.try_create_connection(downstream)
            log(f"Could not duplicate SpawnAttachments for {setammo_name}")
            continue

        new_exec = new_node.find_input_pin("execute")
        new_self = new_node.find_input_pin("self")
        new_then = new_node.find_then_pin()
        spawned_pin = spawned_item_get.find_output_pin("SpawnedItem")

        if not (new_exec and new_self and new_then and spawned_pin):
            editor.remove_nodes([new_node])
            then_pin.try_create_connection(downstream)
            log(f"SpawnAttachments duplicate missing pins for {setammo_name}")
            continue

        then_pin.try_create_connection(new_exec)
        spawned_pin.try_create_connection(new_self)
        new_then.try_create_connection(downstream)
        log(f"Wired {setammo_name} -> SpawnAttachments -> downstream")


def fix_sniper_weapon_defaults() -> None:
    sniper_bp = unreal.load_asset(f"{SNIPER_BP}.BP_Weapon_Sniper")
    scope_mesh = unreal.load_asset(f"{SCOPE_MESH}.{SCOPE_MESH.split('/')[-1]}")

    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    for handle in sds.k2_gather_subobject_data_for_blueprint(sniper_bp):
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
        if not obj or obj.get_name() != "OpticSight_GEN_VARIABLE":
            continue
        obj.set_editor_property("static_mesh", scope_mesh)
        log("Set OpticSight_GEN_VARIABLE static_mesh to SM_4xScopeForSniper")

    cdo = unreal.get_default_object(sniper_bp.generated_class())
    aim = float(cdo.get_editor_property("AimDistanceFromCamera"))
    if aim < 12.0:
        cdo.set_editor_property("AimDistanceFromCamera", 15.0)
        log(f"AimDistanceFromCamera {aim} -> 15.0")

    sniper_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(sniper_bp)
    unreal.EditorAssetLibrary.save_asset(SNIPER_BP, only_if_is_dirty=False)


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    char_bp = unreal.load_asset(f"{CHAR_BP}.BP_FPCharacter")
    if not char_bp:
        raise RuntimeError("Missing BP_FPCharacter")

    fix_hands_slot_loadout(char_bp)
    fix_fallback_ammo(char_bp)
    try:
        insert_spawn_attachments_after_setammo(char_bp)
    except Exception as exc:
        log(f"SpawnAttachments wiring failed: {exc}")

    unreal.BlueprintEditorLibrary.compile_blueprint(char_bp)
    unreal.EditorAssetLibrary.save_asset(CHAR_BP, only_if_is_dirty=False)

    fix_sniper_weapon_defaults()
    log("Done")


main()
