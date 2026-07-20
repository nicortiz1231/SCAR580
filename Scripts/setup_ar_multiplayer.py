"""Wire AR multiplayer prototype: game mode, replicated pawn components, opponent raycast hits."""

import unreal
from pathlib import Path

LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/setup_ar_multiplayer.log")

GM_AR = "/Game/SCAR580/Blueprints/GameModes/GM_SCAR_AR"
GM_AR_MP = "/Game/SCAR580/Blueprints/GameModes/GM_SCAR_AR_Multiplayer"
BP_FP_CHARACTER = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ITEM_BASE = "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base"
MAP_AR = "/Game/SCAR580/Maps/Map_AR"

GM_MP_CLASS = "/Script/SCAR.SCARARMultiplayerGameMode"
PC_MP_CLASS = "/Script/SCAR.SCARARMultiplayerPlayerController"

POSE_SYNC_CLASS = "/Script/SCAR.SCARARPoseSyncComponent"
PRESENTATION_CLASS = "/Script/SCAR.SCARMultiplayerPresentationComponent"
HEALTH_CLASS = "/Script/SCAR.SCARMultiplayerHealthComponent"
COMBAT_CLASS = "/Script/SCAR.SCARMultiplayerCombatComponent"

OPPONENT_MANNEQUIN_MESH = (
    "/Game/BodycamFPSKIT/Demo/Character/Mannequins/Meshes/SKM_Manny.SKM_Manny"
)
OPPONENT_FP_ARMS_MESH = "/Game/BodycamFPSKIT/Blueprints/Camera/SKM_Camera.SKM_Camera"
OPPONENT_MIRROR_ANIM = (
    "/Game/BodycamFPSKIT/Demo/Character/Mannequins/Animations/ABP_Mirror.ABP_Mirror_C"
)
OPPONENT_POSE_DRIVER_ANIM = (
    "/Game/BodycamFPSKIT/Character/ABP_FP_ArmsProcedural.ABP_FP_ArmsProcedural_C"
)
OPPONENT_PISTOL_MESH = (
    "/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Pistol/Weapon/SKM_Pistol.SKM_Pistol"
)

TRY_MP_SHOT_FN = "/Script/SCAR.SCARMultiplayerCombatBlueprintLibrary:TryApplyMultiplayerOpponentShot"
FIRE_HITSCAN_FN = (
    "/Script/Engine.BlueprintGeneratedClass'"
    "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base_C:Fire_HitScan'"
)


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[setup_ar_multiplayer] {msg}")


def set_prop(obj, names, value) -> bool:
    for name in names:
        try:
            obj.set_editor_property(name, value)
            log(f"Set {obj.get_name()}.{name} = {value}")
            return True
        except Exception as exc:
            log(f"Skip {name}: {exc}")
    return False


def blueprint_has_component(bp, class_name_substring: str) -> bool:
    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = subsystem.k2_gather_subobject_data_for_blueprint(bp)
    for handle in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
        if obj and class_name_substring in obj.get_class().get_name():
            return True
    return False


def add_component(bp, component_class_path: str, component_name: str) -> None:
    if blueprint_has_component(bp, component_name):
        log(f"{bp.get_name()} already has {component_name}")
        return

    component_class = unreal.load_class(None, component_class_path)
    if not component_class:
        log(f"{component_class_path} not compiled yet; build C++ first")
        return

    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = subsystem.k2_gather_subobject_data_for_blueprint(bp)
    root_handle = handles[0] if handles else None
    if not root_handle:
        raise RuntimeError(f"Could not resolve root subobject for {bp.get_name()}")

    params = unreal.AddNewSubobjectParams()
    params.parent_handle = root_handle
    params.new_class = component_class
    params.blueprint_context = bp

    result, fail_reason = subsystem.add_new_subobject(params)
    if fail_reason and str(fail_reason).strip():
        raise RuntimeError(f"Failed to add {component_name}: {fail_reason}")

    subsystem.rename_subobject(result, component_name)
    log(f"Added {component_name} to {bp.get_name()}")


def ensure_multiplayer_game_mode() -> None:
    ensure_directory = "/Game/SCAR580/Blueprints/GameModes"
    if not unreal.EditorAssetLibrary.does_directory_exist(ensure_directory):
        unreal.EditorAssetLibrary.make_directory(ensure_directory)

    if not unreal.EditorAssetLibrary.does_asset_exist(GM_AR):
        raise RuntimeError(f"Missing base game mode {GM_AR}")

    if not unreal.EditorAssetLibrary.does_asset_exist(GM_AR_MP):
        duplicated = unreal.EditorAssetLibrary.duplicate_asset(GM_AR, GM_AR_MP)
        if not duplicated:
            raise RuntimeError(f"Failed to duplicate {GM_AR} -> {GM_AR_MP}")
        log(f"Created {GM_AR_MP}")

    gm_bp = unreal.load_asset(f"{GM_AR_MP}.GM_SCAR_AR_Multiplayer")
    gm_class = unreal.load_class(None, GM_MP_CLASS)
    pc_class = unreal.load_class(None, PC_MP_CLASS)
    pawn_class = unreal.load_class(None, f"{BP_FP_CHARACTER}.BP_FPCharacter_C")

    if not gm_class or not pc_class or not pawn_class:
        raise RuntimeError("Missing compiled multiplayer C++ classes; build SCAR module first")

    cdo = unreal.get_default_object(gm_bp.generated_class())
    set_prop(cdo, ("default_pawn_class", "DefaultPawnClass"), pawn_class)
    set_prop(cdo, ("player_controller_class", "PlayerControllerClass"), pc_class)

    current_parent = unreal.BlueprintEditorLibrary.get_blueprint_parent_class(gm_bp)
    if current_parent != gm_class:
        unreal.BlueprintEditorLibrary.reparent_blueprint(gm_bp, gm_class)
        log(f"Reparented {GM_AR_MP} -> {GM_MP_CLASS}")
    else:
        log(f"{GM_AR_MP} already parented to {GM_MP_CLASS}")

    unreal.BlueprintEditorLibrary.compile_blueprint(gm_bp)
    unreal.EditorAssetLibrary.save_asset(GM_AR_MP, only_if_is_dirty=False)
    log("Configured GM_SCAR_AR_Multiplayer")


def find_component_on_cdo(cdo, component_name: str):
    for component in cdo.get_components_by_class(unreal.ActorComponent.static_class()):
        name = component.get_name()
        class_name = component.get_class().get_name()
        if name.startswith(component_name) or component_name in class_name:
            return component
    return None


def configure_presentation_component(bp) -> None:
    cdo = unreal.get_default_object(bp.generated_class())
    presentation = find_component_on_cdo(cdo, "SCARMultiplayerPresentation")
    if not presentation:
        log("SCARMultiplayerPresentation component not found on BP_FPCharacter CDO")
        return

    mannequin_mesh = unreal.load_asset(OPPONENT_MANNEQUIN_MESH)
    fp_arms_mesh = unreal.load_asset(OPPONENT_FP_ARMS_MESH)
    pistol_mesh = unreal.load_asset(OPPONENT_PISTOL_MESH)
    mirror_anim = unreal.load_class(None, OPPONENT_MIRROR_ANIM)
    pose_anim = unreal.load_class(None, OPPONENT_POSE_DRIVER_ANIM)
    set_prop(presentation, ("opponent_mannequin_mesh", "OpponentMannequinMesh"), mannequin_mesh)
    set_prop(presentation, ("opponent_fp_arms_mesh", "OpponentFpArmsMesh"), fp_arms_mesh)
    set_prop(presentation, ("opponent_fallback_pistol_mesh", "OpponentFallbackPistolMesh"), pistol_mesh)
    set_prop(presentation, ("opponent_mirror_anim_class", "OpponentMirrorAnimClass"), mirror_anim)
    set_prop(presentation, ("opponent_pose_driver_anim_class", "OpponentPoseDriverAnimClass"), pose_anim)
    set_prop(
        presentation,
        ("opponent_weapon_attach_socket_name", "OpponentWeaponAttachSocketName"),
        "ik_hand_gun",
    )
    set_prop(
        presentation,
        ("pose_driver_relative_location", "PoseDriverRelativeLocation"),
        unreal.Vector(15.0, 0.0, 65.0),
    )
    set_prop(presentation, ("b_show_opponent_debug", "bShowOpponentDebug"), False)
    set_prop(presentation, ("b_place_opponent_in_view", "bPlaceOpponentInView"), False)
    log("Configured SCARMultiplayerPresentation mirror mannequin + FP pose driver")


def configure_replicated_character() -> None:
    bp = unreal.load_asset(f"{BP_FP_CHARACTER}.BP_FPCharacter")
    if not bp:
        raise RuntimeError(f"Missing {BP_FP_CHARACTER}")

    cdo = unreal.get_default_object(bp.generated_class())
    set_prop(cdo, ("bReplicates",), True)
    set_prop(cdo, ("bReplicateMovement",), False)
    set_prop(cdo, ("only_relevant_to_owner", "bOnlyRelevantToOwner"), False)
    set_prop(cdo, ("always_relevant", "bAlwaysRelevant"), True)

    add_component(bp, POSE_SYNC_CLASS, "SCARARPoseSync")
    add_component(bp, PRESENTATION_CLASS, "SCARMultiplayerPresentation")
    add_component(bp, HEALTH_CLASS, "SCARMultiplayerHealth")
    add_component(bp, COMBAT_CLASS, "SCARMultiplayerCombat")

    configure_presentation_component(bp)

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_FP_CHARACTER, only_if_is_dirty=False)
    log("Configured BP_FPCharacter for multiplayer replication")


def connect_data(src, dst) -> bool:
    if src and dst:
        return bool(src.try_create_connection(dst))
    return False


def connect_exec(src, dst) -> bool:
    if src and dst:
        return bool(src.try_create_connection(dst))
    return False


def title(node) -> str:
    return str(node.get_node_title()).replace("\n", " | ")


def links(pin):
    if not pin:
        return []
    try:
        return list(pin.list_connected_pins())
    except Exception:
        return list(unreal.BlueprintGraphPinLibrary.list_connected_pins(pin))


def insert_after(exec_out, node):
    downstream = [p for p in links(exec_out) if p.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT]
    exe_in = node.find_input_pin("execute")
    exe_out = node.find_output_pin("then")
    if not exe_in or not exe_out:
        return False
    exec_out.break_pin_links()
    if not connect_exec(exec_out, exe_in):
        return False
    for d in downstream:
        connect_exec(exe_out, d)
    return True


def remove_broken_multiplayer_phys_nodes(bp) -> None:
    """Remove invalid AfterPhysicsHit nodes that block blueprint compile."""
    for graph in unreal.BlueprintEditorLibrary.list_graphs(bp):
        if graph.get_name() != "Fire_HitScan":
            continue
        editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        broken = [
            n
            for n in editor.list_all_nodes()
            if "TryApplyMultiplayerOpponentShotAfterPhysicsHit" in title(n)
        ]
        for node in broken:
            editor.remove_nodes([node])
            log(f"Removed broken {node.get_name()} from Fire_HitScan")


def wire_weapon_multiplayer_shot() -> None:
    bp = unreal.load_asset(f"{BP_ITEM_BASE}.BP_Item_Base")
    if not bp:
        raise RuntimeError(f"Missing {BP_ITEM_BASE}")

    remove_broken_multiplayer_phys_nodes(bp)

    eg = next(g for g in unreal.BlueprintEditorLibrary.list_graphs(bp) if g.get_name() == "EventGraph")
    ed = unreal.BlueprintGraphEditor.get_graph_editor(eg)

    trigger = next(
        (
            n
            for n in ed.list_all_nodes()
            if title(n) == "Trigger" and n.get_class().get_name() == "K2Node_CustomEvent"
        ),
        None,
    )
    if not trigger:
        log("Trigger event not found on BP_Item_Base EventGraph")
        return

    mp_shot = next((n for n in ed.list_all_nodes() if "TryApplyMultiplayerOpponentShot" in title(n)), None)
    if not mp_shot:
        mp_shot = ed.add_call_function_node(TRY_MP_SHOT_FN)
        log("Created TryApplyMultiplayerOpponentShot on EventGraph")

    for pin_name, value in (("BaseDamage", "25.0"),):
        pin = mp_shot.find_input_pin(pin_name)
        if pin and not links(pin):
            pin.set_pin_value(value)
    crit = mp_shot.find_input_pin("CriticalMultiplier")
    if crit and not links(crit):
        crit.set_pin_value("2.0")

    ar_shot = next((n for n in ed.list_all_nodes() if "TryApplyARBodyShot" in title(n)), None)
    hitscan = next(
        (
            n
            for n in ed.list_all_nodes()
            if ("Fire HitScan" in title(n) or "Fire_HitScan" in title(n))
            and n.get_class().get_name() == "K2Node_CallFunction"
        ),
        None,
    )

    insert_target = ar_shot or hitscan
    if insert_target:
        trigger_then = trigger.find_output_pin("then")
        insert_after(trigger_then, mp_shot)
        if ar_shot:
            mp_then = mp_shot.find_output_pin("then")
            ar_exec = ar_shot.find_input_pin("execute")
            if mp_then and ar_exec and not links(ar_exec):
                connect_exec(mp_then, ar_exec)
        elif hitscan:
            mp_then = mp_shot.find_output_pin("then")
            hs_exec = hitscan.find_input_pin("execute")
            if mp_then and hs_exec and not links(hs_exec):
                connect_exec(mp_then, hs_exec)
        log("Wired Trigger -> TryApplyMultiplayerOpponentShot")

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_ITEM_BASE, only_if_is_dirty=False)


def configure_map_default_game_mode() -> None:
    unreal.EditorLoadingAndSavingUtils.load_map(MAP_AR)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not world:
        log("Editor world unavailable; skipped map game mode patch")
        return

    gm_class = unreal.load_class(None, f"{GM_AR_MP}.GM_SCAR_AR_Multiplayer_C")
    if gm_class:
        world.get_world_settings().set_editor_property("default_game_mode", gm_class)
        unreal.EditorLoadingAndSavingUtils.save_map(unreal.load_asset(MAP_AR), MAP_AR)
        log("Set Map_AR default game mode to GM_SCAR_AR_Multiplayer")


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    ensure_multiplayer_game_mode()

    # Fix weapon blueprint compile issues before touching dependent assets.
    bp_item = unreal.load_asset(f"{BP_ITEM_BASE}.BP_Item_Base")
    if bp_item:
        remove_broken_multiplayer_phys_nodes(bp_item)
        unreal.EditorAssetLibrary.save_asset(BP_ITEM_BASE, only_if_is_dirty=False)

    configure_replicated_character()
    wire_weapon_multiplayer_shot()
    configure_map_default_game_mode()
    log("AR multiplayer setup complete")


main()
