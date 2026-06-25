"""Reset sniper to pristine Bodycam pickup behavior — from scratch."""
import shutil
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/reset_sniper_bodycam_scratch.log")
ORIG = Path("/Users/nickortiz/Documents/Unreal Projects/BODYCAMFPSKIT/Content/BodycamFPSKIT/Blueprints/Interactables")
SCAR = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Content/BodycamFPSKIT/Blueprints/Interactables")
CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
ITEM_BP = "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base"
SNIPER_BP = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper"
SET_WEAPON_AMMO_FN = f"{ITEM_BP}.BP_Item_Base_C:SetWeaponAmmoData"
SPAWN_ATT_FN = f"{ITEM_BP}.BP_Item_Base_C:SpawnAttachments"
SET_AMMO_FN = f"{ITEM_BP}.BP_Item_Base_C:SetAmmo"

# BP_Weapon_Pickup_Sniper / Map_Test defaults
PICKUP_ITEMDATA = {
    "ItemData_Attachments_34_07B0276F4133E43075B4B699D3A93393": (
        "(Sight_37_688233D743AA415C91250EBC240B11ED=NewEnumerator1,"
        "Laser_38_3209213B48BBF0256E8473A33CC4C0FE=NewEnumerator1,"
        "Muzzle_42_288332C341D7A8B7E31632867A1FE4DB=NewEnumerator1,"
        "Grip_46_62A21AB489496DC33D1ACDA661CA2D84=NewEnumerator0)"
    ),
    "ItemData_AmmoCount_5_529648E9447E28C3BF4E468F960E71F2": "12",
    "ItemData_MaxAmmo_7_3209213B48BBF0256E8473A33CC4C0FE": "120",
}

RESTORE_FILES = (
    (ORIG / "Sniper/BP_Weapon_Sniper.uasset", SCAR / "Sniper/BP_Weapon_Sniper.uasset"),
    (ORIG / "Sniper/DT_SniperAnimationValues.uasset", SCAR / "Sniper/DT_SniperAnimationValues.uasset"),
    (ORIG / "Sniper/BP_Weapon_Pickup_Sniper.uasset", SCAR / "Sniper/BP_Weapon_Pickup_Sniper.uasset"),
)


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[reset_sniper] {msg}")


def connect_exec(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def connect_data(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def find_node(editor, name):
    for node in editor.list_all_nodes():
        if node.get_name() == name:
            return node
    return None


def output_pin(node, preferred=None):
    if preferred:
        p = node.find_output_pin(preferred)
        if p:
            return p
    for p in unreal.BlueprintEditorLibrary.list_all_pins(node):
        if unreal.BlueprintGraphPinLibrary.get_pin_direction(p) == unreal.EdGraphPinDirection.EGPD_OUTPUT:
            return p
    return None


def restore_disk_assets() -> None:
    for src, dst in RESTORE_FILES:
        if not src.exists():
            raise FileNotFoundError(f"Missing original: {src}")
        shutil.copy2(src, dst)
        log(f"Restored {dst.name} ({dst.stat().st_size} bytes)")


def is_scope_hack_node(node) -> bool:
    cls = node.get_class().get_name()
    title = str(node.get_node_title())
    if cls == "K2Node_VariableGet" and ("ScopeSightMesh" in title or "OpticSight" in title):
        return True
    if cls == "K2Node_IfThenElse":
        cond = node.find_input_pin("Condition")
        if cond:
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(cond):
                o = lp.get_owning_node()
                if "Equal" in str(o.get_node_title()):
                    for pin in unreal.BlueprintEditorLibrary.list_all_pins(o):
                        val = str(unreal.BlueprintGraphPinLibrary.get_pin_value(pin))
                        if "SM_4xScopeForSniper" in val:
                            return True
    if cls == "K2Node_CallFunction" and "SetStaticMesh" in title:
        mesh_pin = node.find_input_pin("NewMesh")
        if mesh_pin:
            val = str(unreal.BlueprintGraphPinLibrary.get_pin_value(mesh_pin))
            if "SM_4xScopeForSniper" in val:
                return True
    if cls in ("K2Node_CallFunction",) and "SetVisibility" in title:
        exec_pin = node.find_input_pin("execute")
        if exec_pin:
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(exec_pin):
                prev = lp.get_owning_node()
                if prev.get_class().get_name() == "K2Node_CallFunction" and "SetStaticMesh" in str(prev.get_node_title()):
                    mp = prev.find_input_pin("NewMesh")
                    if mp and "SM_4xScopeForSniper" in str(unreal.BlueprintGraphPinLibrary.get_pin_value(mp)):
                        return True
    if cls == "K2Node_PromotableOperator" and "Equal" in title:
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            val = str(unreal.BlueprintGraphPinLibrary.get_pin_value(pin))
            if "SM_4xScopeForSniper" in val:
                return True
    return False


def remove_scope_hacks_from_graph(editor, graph_label: str) -> int:
    remove = []
    for node in editor.list_all_nodes():
        if is_scope_hack_node(node):
            remove.append(node)
    if not remove:
        return 0
    editor.remove_nodes(remove)
    log(f"Removed {len(remove)} scope hack node(s) from {graph_label}")
    return len(remove)


def clean_character_scope_hacks(char_bp) -> None:
    total = 0
    for graph in unreal.BlueprintEditorLibrary.list_graphs(char_bp):
        editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        total += remove_scope_hacks_from_graph(editor, graph.get_name())
    log(f"Total scope hack nodes removed from character: {total}")


def set_hands_slot_pickup_itemdata(char_bp) -> None:
    for graph in unreal.BlueprintEditorLibrary.list_graphs(char_bp):
        if graph.get_name() != "BeginSetup":
            continue
        editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        for node in editor.list_all_nodes():
            if node.get_name() != "K2Node_GenericCreateObject_2":
                continue
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                if pname in PICKUP_ITEMDATA:
                    pin.set_pin_value(PICKUP_ITEMDATA[pname])
                    log(f"HandsSlot {pname} -> {PICKUP_ITEMDATA[pname]}")
            return
    log("WARN: HandsSlot node not found")


def get_downstream_exec(exec_out_pin):
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(exec_out_pin):
        if lp.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT:
            return lp
    return None


def ensure_sniper_spawn_pickup_chain(char_bp) -> None:
    """Spawn -> Set SpawnedItem -> SetWeaponAmmoData -> SetAmmo(12,120) -> SpawnAttachments -> downstream."""
    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
    )

    set_spawned = find_node(editor, "K2Node_VariableSet_15")
    if not set_spawned:
        raise RuntimeError("Missing K2Node_VariableSet_15 (Set SpawnedItem)")

    spawned_out = output_pin(set_spawned, "Output_Get")
    if not spawned_out:
        spawned_out = output_pin(set_spawned)

    then_pin = set_spawned.find_output_pin("then")
    # Must continue into procedural setup — never wire back to SetWeaponAmmoData (infinite loop).
    downstream = find_node(editor, "K2Node_VariableGet_83")
    downstream_exec = downstream.find_input_pin("execute") if downstream else None

    set_weapon_ammo = find_node(editor, "K2Node_CallFunction_157")
    set_ammo = find_node(editor, "K2Node_CallFunction_212")
    spawn_att = find_node(editor, "K2Node_CallFunction_141")

    if not set_weapon_ammo:
        set_weapon_ammo = editor.add_call_function_node(SET_WEAPON_AMMO_FN)
    if not set_ammo:
        set_ammo = editor.add_call_function_node(SET_AMMO_FN)
    if not spawn_att:
        spawn_att = editor.add_call_function_node(SPAWN_ATT_FN)

    if not all((set_weapon_ammo, set_ammo, spawn_att)):
        raise RuntimeError("Failed creating spawn chain nodes")

    connect_data(spawned_out, set_weapon_ammo.find_input_pin("self"))
    connect_data(spawned_out, set_ammo.find_input_pin("self"))
    connect_data(spawned_out, spawn_att.find_input_pin("self"))

    pickup_pin = set_weapon_ammo.find_input_pin("IsPickUp")
    if pickup_pin:
        pickup_pin.set_pin_value("false")

    ammo_pin = set_ammo.find_input_pin("AmmoCount")
    max_pin = set_ammo.find_input_pin("MaxAmmo")
    if ammo_pin:
        ammo_pin.set_pin_value("12")
    if max_pin:
        max_pin.set_pin_value("120")

    then_pin.break_pin_links()
    connect_exec(then_pin, set_weapon_ammo.find_input_pin("execute"))
    connect_exec(set_weapon_ammo.find_output_pin("then"), set_ammo.find_input_pin("execute"))
    connect_exec(set_ammo.find_output_pin("then"), spawn_att.find_input_pin("execute"))
    if downstream_exec:
        connect_exec(spawn_att.find_output_pin("then"), downstream_exec)
    log("Wired sniper spawn: SetWeaponAmmoData -> SetAmmo(12,120) -> SpawnAttachments -> VariableGet_83")


def verify(sniper_bp, char_bp) -> None:
    sniper_eg = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(sniper_bp)
    )
    scope_nodes = sum(1 for n in sniper_eg.list_all_nodes() if "SetStaticMesh" in str(n.get_node_title()))
    log(f"VERIFY sniper EventGraph SetStaticMesh nodes={scope_nodes} (expect 0)")

    cdo = unreal.get_default_object(sniper_bp.generated_class())
    log(
        f"VERIFY sniper AimDistance={cdo.get_editor_property('AimDistanceFromCamera')} "
        f"Scope={cdo.get_editor_property('ScopeSightMesh').get_name()} "
        f"OpticRail={cdo.get_editor_property('OpticSightMesh').get_name()}"
    )

    char_eg = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
    )
    hacks = sum(1 for n in char_eg.list_all_nodes() if is_scope_hack_node(n))
    log(f"VERIFY character scope hack nodes remaining={hacks} (expect 0)")

    for name in ("K2Node_CallFunction_157", "K2Node_CallFunction_212", "K2Node_CallFunction_141"):
        node = find_node(char_eg, name)
        log(f"VERIFY {name} present={node is not None}")


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    restore_disk_assets()

    char_bp = unreal.load_asset(f"{CHAR_BP}.BP_FPCharacter")
    sniper_bp = unreal.load_asset(f"{SNIPER_BP}.BP_Weapon_Sniper")
    if not char_bp or not sniper_bp:
        raise RuntimeError("Missing blueprints")

    clean_character_scope_hacks(char_bp)
    set_hands_slot_pickup_itemdata(char_bp)
    ensure_sniper_spawn_pickup_chain(char_bp)

    for bp, path in ((char_bp, CHAR_BP),):
        bp.modify()
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)

    # Reload sniper from disk (never save — editor cache would re-pollute the restored asset).
    sniper_bp = unreal.load_asset(f"{SNIPER_BP}.BP_Weapon_Sniper")

    # HandsSlot pins can reset on compile
    set_hands_slot_pickup_itemdata(char_bp)
    char_bp.modify()
    unreal.EditorAssetLibrary.save_asset(CHAR_BP, only_if_is_dirty=False)

    verify(sniper_bp, char_bp)
    log("Done — sniper reset to Bodycam pickup flow")


main()
