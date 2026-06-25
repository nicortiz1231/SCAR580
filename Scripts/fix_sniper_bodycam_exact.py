"""Restore Bodycam sniper visuals: SpawnAttachments scope + Map_Test pickup ItemData on wheel spawn."""
import shutil
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_sniper_bodycam_exact.log")
ORIG = Path("/Users/nickortiz/Documents/Unreal Projects/BODYCAMFPSKIT/Content/BodycamFPSKIT/Blueprints/Interactables")
SCAR = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Content/BodycamFPSKIT/Blueprints/Interactables")
CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
ITEM_BP = "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base"
SNIPER_BP = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper"
SCOPE_MESH = "/Game/BodycamFPSKIT/Demo/Meshes/SM_4xScopeForSniper.SM_4xScopeForSniper"
SET_STATIC_MESH_FN = "/Script/Engine.StaticMeshComponent:SetStaticMesh"
SET_VISIBILITY_FN = "/Script/Engine.SceneComponent:SetVisibility"
SET_WEAPON_AMMO_FN = f"{ITEM_BP}.BP_Item_Base_C:SetWeaponAmmoData"

# BP_Weapon_Pickup_Sniper defaults (Map_Test)
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

RESTORE_FILES = (
    (ORIG / "Sniper/BP_Weapon_Sniper.uasset", SCAR / "Sniper/BP_Weapon_Sniper.uasset"),
    (ORIG / "Sniper/DT_SniperAnimationValues.uasset", SCAR / "Sniper/DT_SniperAnimationValues.uasset"),
    (ORIG / "BP_Item_Base.uasset", SCAR / "BP_Item_Base.uasset"),
)


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[bodycam_exact] {msg}")


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


def restore_assets() -> None:
    for src, dst in RESTORE_FILES:
        if not src.exists():
            raise FileNotFoundError(f"Missing original asset: {src}")
        shutil.copy2(src, dst)
        log(f"Restored {dst.name} ({dst.stat().st_size} bytes)")


def wire_scope_on_exec(editor, exec_pin) -> None:
    """SpawnAttachments: SetStaticMesh(OpticSight, ScopeSightMesh) -> SetVisibility(true)."""
    if not exec_pin:
        raise RuntimeError("Missing exec pin for scope wiring")

    downstream = []
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(exec_pin):
        if lp.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT:
            downstream.append(lp)

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

    if downstream:
        exec_pin.break_pin_links()
        connect_exec(exec_pin, set_mesh.find_input_pin("execute"))
        connect_exec(set_mesh.find_output_pin("then"), set_vis.find_input_pin("execute"))
        for pin in downstream:
            connect_exec(set_vis.find_output_pin("then"), pin)
    else:
        connect_exec(exec_pin, set_mesh.find_input_pin("execute"))
        connect_exec(set_mesh.find_output_pin("then"), set_vis.find_input_pin("execute"))


def has_spawnattachments_scope(editor) -> bool:
    for node in editor.list_all_nodes():
        title = str(node.get_node_title())
        if "SpawnAttachments" not in title and node.get_class().get_name() != "K2Node_CustomEvent":
            continue
        if "SpawnAttachments" not in title:
            continue
        then = node.find_output_pin("then")
        if not then:
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
            if "SetStaticMesh" in str(lp.get_owning_node().get_node_title()):
                return True
    return False


def ensure_spawnattachments_scope(bp, label: str) -> None:
    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(bp)
    )
    if has_spawnattachments_scope(editor):
        log(f"{label} SpawnAttachments already applies scope")
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
        raise RuntimeError(f"Could not create SpawnAttachments on {label}")

    wire_scope_on_exec(editor, spawn_event.find_output_pin("then"))
    log(f"Wired {label} SpawnAttachments -> ScopeSightMesh on OpticSight")


def remove_broken_beginplay_scope(sniper_bp) -> None:
    """Remove any hacked BeginPlay/UCS scope nodes; keep stock parent-only graphs."""
    for graph_name in ("EventGraph", "UserConstructionScript"):
        graph = None
        for g in unreal.BlueprintEditorLibrary.list_graphs(sniper_bp):
            if g.get_name() == graph_name:
                graph = g
                break
        if not graph:
            continue
        editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        remove = []
        for node in editor.list_all_nodes():
            if node.get_class().get_name() != "K2Node_CallFunction":
                continue
            title = str(node.get_node_title())
            if "SetStaticMesh" not in title and "SetVisibility" not in title:
                continue
            remove.append(node)
        for node in editor.list_all_nodes():
            if node.get_class().get_name() == "K2Node_VariableGet":
                title = str(node.get_node_title())
                if "OpticSight" in title or "ScopeSightMesh" in title:
                    remove.append(node)
        remove = list({id(n): n for n in remove}.values())
        if remove:
            editor.remove_nodes(remove)
            log(f"Removed {len(remove)} broken scope node(s) from sniper {graph_name}")


def ensure_sniper_cdo(sniper_bp) -> None:
    scope_mesh = unreal.load_asset(SCOPE_MESH)
    cdo = unreal.get_default_object(sniper_bp.generated_class())
    cdo.set_editor_property("ScopeSightMesh", scope_mesh)
    # Stock Bodycam: OpticSightMesh = rail (SM_SightSniper), not the 4x glass.
    log(
        f"Sniper CDO AimDistance={cdo.get_editor_property('AimDistanceFromCamera')} "
        f"Scope={cdo.get_editor_property('ScopeSightMesh').get_name()} "
        f"Optic={cdo.get_editor_property('OpticSightMesh').get_name()}"
    )


def fix_hands_slot(char_bp) -> bool:
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
                log(f"HandsSlot attachments -> {unreal.BlueprintGraphPinLibrary.get_pin_value(pin)}")
                return True
    log("WARN: HandsSlot construct node not found")
    return False


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
            log(f"{spawn_name} already connected to {get_name}")
            continue
        then.break_pin_links()
        connect_exec(then, exec_in)
        log(f"Reconnected {spawn_name} -> {get_name}")


def insert_sniper_setweaponammo(char_bp) -> None:
    """Map_Test pickup calls SetWeaponAmmoData before attachments; wheel spawn must too."""
    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
    )

    set_spawned = setammo = None
    for node in editor.list_all_nodes():
        if node.get_name() == "K2Node_VariableSet_15":
            set_spawned = node
        if node.get_name() == "K2Node_CallFunction_212":
            setammo = node

    if not set_spawned or not setammo:
        log("SKIP SetWeaponAmmoData: sniper spawn nodes not found")
        return

    # Already inserted?
    spawned_then = set_spawned.find_output_pin("then")
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(spawned_then):
        if "SetWeaponAmmoData" in str(lp.get_owning_node().get_node_title()):
            log("SetWeaponAmmoData already on sniper spawn path")
            return

    set_weapon_ammo = editor.add_call_function_node(SET_WEAPON_AMMO_FN)
    if not set_weapon_ammo:
        raise RuntimeError("Failed creating SetWeaponAmmoData node")

    connect_data(set_spawned.find_output_pin("Output_Get"), set_weapon_ammo.find_input_pin("self"))
    pickup_pin = set_weapon_ammo.find_input_pin("IsPickUp")
    if pickup_pin:
        pickup_pin.set_pin_value("true")

    setammo_exec = setammo.find_input_pin("execute")
    spawned_then.break_pin_links()
    connect_exec(spawned_then, set_weapon_ammo.find_input_pin("execute"))
    connect_exec(set_weapon_ammo.find_output_pin("then"), setammo_exec)
    log("Inserted SetWeaponAmmoData on sniper wheel spawn (Map_Test pickup parity)")


def verify(char_bp, sniper_bp, item_bp) -> None:
    # HandsSlot
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
                    log(f"VERIFY HandsSlot {pname}={unreal.BlueprintGraphPinLibrary.get_pin_value(pin)}")

    cdo = unreal.get_default_object(sniper_bp.generated_class())
    log(
        f"VERIFY sniper nodes={len(unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(sniper_bp)).list_all_nodes())} "
        f"AimDistance={cdo.get_editor_property('AimDistanceFromCamera')}"
    )

    for label, bp in (("sniper", sniper_bp),):
        editor = unreal.BlueprintGraphEditor.get_graph_editor(
            unreal.BlueprintEditorLibrary.find_event_graph(bp)
        )
        log(f"VERIFY {label} SpawnAttachments scope wired={has_spawnattachments_scope(editor)}")


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    restore_assets()

    item_bp = unreal.load_asset(f"{ITEM_BP}.BP_Item_Base")
    sniper_bp = unreal.load_asset(f"{SNIPER_BP}.BP_Weapon_Sniper")
    char_bp = unreal.load_asset(f"{CHAR_BP}.BP_FPCharacter")
    if not all((item_bp, sniper_bp, char_bp)):
        raise RuntimeError("Missing blueprints after restore")

    remove_broken_beginplay_scope(sniper_bp)
    ensure_spawnattachments_scope(sniper_bp, "Sniper")
    ensure_sniper_cdo(sniper_bp)

    fix_hands_slot(char_bp)
    insert_sniper_setweaponammo(char_bp)
    reconnect_spawn_chains(char_bp)

    for bp, path in (
        (sniper_bp, SNIPER_BP),
        (char_bp, CHAR_BP),
    ):
        bp.modify()
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)

    # Re-apply HandsSlot after compile (pin defaults can reset)
    fix_hands_slot(char_bp)
    char_bp.modify()
    unreal.EditorAssetLibrary.save_asset(CHAR_BP, only_if_is_dirty=False)

    verify(char_bp, sniper_bp, item_bp)
    log("Done")


main()
