"""Restore pre-AR FPS framing, disable fisheye/vignette, keep AR passthrough independent."""

import unreal
from pathlib import Path

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
AC_BODY_CAM = "/Game/BodycamFPSKIT/Blueprints/Components/AC_BodycamCamera"
M_OUTLINE = "/Game/BodycamFPSKIT/Blueprints/Materials/M_Outline"
M_FISHEYE_INST = "/Game/BodycamFPSKIT/Blueprints/Camera/Materials/M_FishEyeLens_Inst"
M_FISHEYE_INST_ASSET = f"{M_FISHEYE_INST}.M_FishEyeLens_Inst"
M_VIGNETTE = "/Game/BodycamFPSKIT/Blueprints/Camera/Materials/M_Vignette"
M_VIGNETTE_ASSET = f"{M_VIGNETTE}.M_Vignette"
MPC_VIGNETTE = "/Game/BodycamFPSKIT/Blueprints/Camera/Materials/MPC_Vignette"
AR_SESSION = "/Game/HandheldAR/D_ARSessionConfig"
MAP_AR = "/Game/SCAR580/Maps/Map_AR"
STRIP_MARKER = "AR Strip Lens Effects"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_ar_view_restore.log")
ADD_BLENDABLE_FN = "/Script/Engine.CameraComponent.AddOrUpdateBlendable"


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[fix_ar_view_restore] {msg}")


def set_prop(obj, names, value) -> bool:
    label = obj.get_name() if hasattr(obj, "get_name") else type(obj).__name__
    for name in names:
        try:
            obj.set_editor_property(name, value)
            log(f"Set {label}.{name} = {value}")
            return True
        except Exception as exc:
            log(f"Skip {label}.{name}: {exc}")
    return False


def pin_value(pin, value: str) -> None:
    if pin:
        pin.set_pin_value(value)


def connect_exec(src, dst) -> None:
    if not src or not dst:
        raise RuntimeError("Missing exec pin")
    if not src.try_create_connection(dst):
        raise RuntimeError("Exec connection failed")


def connect_data(src, dst) -> None:
    if not src or not dst:
        raise RuntimeError("Missing data pin")
    if not src.try_create_connection(dst):
        raise RuntimeError("Data connection failed")


def configure_post_process_settings(settings, label: str) -> None:
    set_prop(settings, ("override_auto_exposure_method", "b_override_auto_exposure_method"), True)
    set_prop(settings, ("auto_exposure_method",), unreal.AutoExposureMethod.AEM_MANUAL)
    set_prop(settings, ("override_auto_exposure_bias", "b_override_auto_exposure_bias"), True)
    set_prop(settings, ("auto_exposure_bias",), 1.0)
    set_prop(settings, ("override_auto_exposure_min_brightness", "b_override_auto_exposure_min_brightness"), True)
    set_prop(settings, ("auto_exposure_min_brightness",), 1.0)
    set_prop(settings, ("override_auto_exposure_max_brightness", "b_override_auto_exposure_max_brightness"), True)
    set_prop(settings, ("auto_exposure_max_brightness",), 1.0)
    set_prop(settings, ("override_auto_exposure_apply_physical_camera_exposure",), True)
    set_prop(settings, ("auto_exposure_apply_physical_camera_exposure",), False)
    set_prop(settings, ("override_local_exposure_method",), False)
    set_prop(settings, ("override_local_exposure_detail_strength", "b_override_local_exposure_detail_strength"), False)
    log(f"Configured exposure on {label}")


def make_outline_only_blendables() -> unreal.WeightedBlendables:
    outline = unreal.load_asset(M_OUTLINE)
    if not outline:
        raise RuntimeError(f"Missing {M_OUTLINE}")
    entry = unreal.WeightedBlendable()
    entry.weight = 1.0
    entry.object = outline
    blendables = unreal.WeightedBlendables()
    blendables.array = [entry]
    return blendables


def set_camera_blendables_outline_only(bp) -> None:
    outline_only = make_outline_only_blendables()
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    for handle in sds.k2_gather_subobject_data_for_blueprint(bp):
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
        if not obj or "FirstPersonCamera" not in obj.get_name():
            continue
        if "CameraComponent" not in obj.get_class().get_name():
            continue
        settings = obj.post_process_settings
        set_prop(settings, ("weighted_blendables", "WeightedBlendables"), outline_only)
        obj.post_process_settings = settings
        log("FirstPersonCamera template blendables = M_Outline only (no fisheye/vignette)")


def configure_spring_arm(comp) -> None:
    set_prop(comp, ("enable_camera_lag", "b_enable_camera_lag"), False)
    set_prop(comp, ("enable_camera_rotation_lag", "b_enable_camera_rotation_lag"), False)
    set_prop(comp, ("use_pawn_control_rotation", "bUsePawnControlRotation"), True)
    set_prop(comp, ("inherit_pitch", "bInheritPitch"), True)
    set_prop(comp, ("inherit_yaw", "bInheritYaw"), True)
    set_prop(comp, ("inherit_roll", "bInheritRoll"), False)
    set_prop(comp, ("target_arm_length", "TargetArmLength"), 0.0)
    set_prop(comp, ("socket_offset", "SocketOffset"), unreal.Vector(0.0, 0.0, 0.0))
    set_prop(comp, ("relative_rotation", "RelativeRotation"), unreal.Rotator(0.0, 0.0, 0.0))
    set_prop(comp, ("target_offset", "TargetOffset"), unreal.Vector(0.0, 0.0, 0.0))


def configure_camera(comp) -> None:
    settings = comp.post_process_settings
    configure_post_process_settings(settings, comp.get_name())
    comp.post_process_settings = settings
    set_prop(comp, ("post_process_blend_weight",), 1.0)
    set_prop(comp, ("use_pawn_control_rotation", "bUsePawnControlRotation"), True)
    set_prop(comp, ("field_of_view", "FieldOfView"), 90.0)


def configure_character_blueprint(bp) -> None:
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    seen = set()
    for handle in sds.k2_gather_subobject_data_for_blueprint(bp):
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
        if not obj:
            continue
        oid = id(obj)
        if oid in seen:
            continue
        seen.add(oid)
        class_name = obj.get_class().get_name()
        if "SpringArmComponent" in class_name:
            configure_spring_arm(obj)
        elif "CameraComponent" in class_name and "FirstPersonCamera" in obj.get_name():
            configure_camera(obj)

    cdo = unreal.get_default_object(bp.generated_class())
    set_prop(cdo, ("BODYCAM",), True)
    set_prop(cdo, ("FOV_Base",), 90.0)
    for comp in cdo.get_components_by_class(unreal.ActorComponent.static_class()):
        if "CharacterMovementComponent" in comp.get_class().get_name():
            set_prop(comp, ("gravity_scale", "GravityScale"), 0.0)

    set_camera_blendables_outline_only(bp)


def disable_bodycam_component_effects() -> None:
    ac = unreal.load_asset(f"{AC_BODY_CAM}.AC_BodycamCamera")
    if not ac:
        log("Missing AC_BodycamCamera")
        return
    cdo = unreal.get_default_object(ac.generated_class())
    set_prop(cdo, ("Camera Shake", "CameraShake"), False)
    unreal.BlueprintEditorLibrary.compile_blueprint(ac)
    unreal.EditorAssetLibrary.save_asset(AC_BODY_CAM, only_if_is_dirty=False)


def zero_material_scalar_parameters(mat_path: str, param_names: tuple[str, ...]) -> None:
    mat = unreal.load_asset(mat_path)
    if not mat:
        log(f"Missing {mat_path}")
        return

    changed = False
    try:
        expressions = mat.get_editor_property("expressions")
    except Exception as exc:
        log(f"Skip {mat_path} expressions: {exc}")
        return

    for expr in expressions:
        if "ScalarParameter" not in expr.get_class().get_name():
            continue
        try:
            name = str(expr.get_editor_property("parameter_name"))
        except Exception:
            continue
        if param_names and name not in param_names:
            continue
        try:
            expr.set_editor_property("default_value", 0.0)
            log(f"Set {mat_path} scalar {name} = 0")
            changed = True
        except Exception as exc:
            log(f"Skip {mat_path}.{name}: {exc}")

    if changed:
        unreal.MaterialEditingLibrary.recompile_material(mat)
        unreal.EditorAssetLibrary.save_asset(mat_path, only_if_is_dirty=False)


def disable_lens_materials() -> None:
    zero_material_scalar_parameters(
        M_FISHEYE_INST,
        ("Intensity", "Density", "Area Radius", "Area Falloff"),
    )
    zero_material_scalar_parameters(
        M_VIGNETTE,
        (
            "Mask Radius",
            "Dark Vignette Radius",
            "Blue Fringe Radius",
            "VignetteIntensity",
            "Intensity",
            "Power",
            "Opacity",
        ),
    )


def node_title(node) -> str:
    try:
        return str(node.get_node_title(unreal.NodeTitleType.FULL_TITLE)).replace("\n", " | ")
    except Exception:
        try:
            return str(node.get_node_title()).replace("\n", " | ")
        except Exception:
            return node.get_name()


def strip_lens_already_wired(editor) -> bool:
    for node in editor.list_all_nodes():
        if node.get_class().get_name() != "K2Node_CallFunction":
            continue
        if "add or update blendable" not in node_title(node).lower():
            continue
        blend_pin = node.find_input_pin("InBlendableObject")
        weight_pin = node.find_input_pin("InWeight")
        if not blend_pin or not weight_pin:
            continue
        blend_val = unreal.BlueprintGraphPinLibrary.get_pin_value(blend_pin) or ""
        weight_val = unreal.BlueprintGraphPinLibrary.get_pin_value(weight_pin) or ""
        if "M_FishEyeLens_Inst" in blend_val and weight_val.startswith("0"):
            return True
    return False


def create_strip_lens_chain(editor, anchor_pos: unreal.IntPoint):
    get_camera = editor.add_get_member_variable_node("FirstPersonCamera")
    strip_fish = editor.add_call_function_node(ADD_BLENDABLE_FN)
    strip_vign = editor.add_call_function_node(ADD_BLENDABLE_FN)
    if not get_camera or not strip_fish or not strip_vign:
        raise RuntimeError("Failed to create strip-lens nodes")

    y = anchor_pos.y + 220
    get_camera.set_node_pos(unreal.IntPoint(anchor_pos.x + 280, y + 120))
    strip_fish.set_node_pos(unreal.IntPoint(anchor_pos.x + 560, y))
    strip_vign.set_node_pos(unreal.IntPoint(anchor_pos.x + 840, y))

    cam_out = get_camera.find_output_pin("FirstPersonCamera")
    if not cam_out:
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(get_camera):
            if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) == unreal.EdGraphPinDirection.EGPD_OUTPUT:
                cam_out = pin
                break
    if not cam_out:
        raise RuntimeError("Could not find FirstPersonCamera output pin")

    for node, mat_asset in ((strip_fish, M_FISHEYE_INST_ASSET), (strip_vign, M_VIGNETTE_ASSET)):
        pin_value(node.find_input_pin("InBlendableObject"), mat_asset)
        pin_value(node.find_input_pin("InWeight"), "0.0")
        connect_data(cam_out, node.find_input_pin("self"))

    connect_exec(strip_fish.find_then_pin(), strip_vign.find_execute_pin())
    return strip_fish, strip_vign


def chain_exec_before(target_exec_pin, first_exec_pin, last_then_pin) -> bool:
    upstream = unreal.BlueprintGraphPinLibrary.list_connected_pins(target_exec_pin)
    if not upstream:
        connect_exec(first_exec_pin, target_exec_pin)
        return False

    upstream_out = upstream[0]
    unreal.BlueprintGraphPinLibrary.break_pin_links(upstream_out)
    connect_exec(upstream_out, first_exec_pin)
    connect_exec(last_then_pin, target_exec_pin)
    return True


BEGIN_SETUP_GRAPH = "BeginSetup"


def macro_is_begin_setup(node) -> bool:
    if node.get_class().get_name() != "K2Node_MacroInstance":
        return False
    title = node_title(node)
    return "Begin Setup" in title or "BeginSetup" in title.replace(" ", "")


def wire_strip_lens_in_begin_setup_macro(bp) -> None:
    graph = None
    for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
        if g.get_name() == BEGIN_SETUP_GRAPH:
            graph = g
            break
    if not graph:
        log("BeginSetup macro graph not found")
        return

    editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    if strip_lens_already_wired(editor):
        log("BeginSetup macro already has strip-lens nodes")
        return

    anchor_node = None
    for node in editor.list_all_nodes():
        try:
            title = str(node.get_node_title()).replace("\n", " | ")
        except Exception:
            continue
        if "ReloadBodycamSettings" in title:
            anchor_node = node
            break

    if not anchor_node:
        log("ReloadBodycamSettings not found in BeginSetup macro")
        return

    pos = anchor_node.get_node_pos()
    strip_fish, strip_vign = create_strip_lens_chain(editor, pos)
    then_pin = anchor_node.find_then_pin()
    downstream = unreal.BlueprintGraphPinLibrary.list_connected_pins(then_pin)
    if downstream:
        chain_exec_before(downstream[0], strip_fish.find_execute_pin(), strip_vign.find_then_pin())
    else:
        connect_exec(then_pin, strip_fish.find_execute_pin())

    log("Hooked strip-lens chain after ReloadBodycamSettings in BeginSetup macro")


def remove_existing_strip_nodes(editor) -> None:
    to_remove = []
    for node in editor.list_all_nodes():
        if node.get_class().get_name() != "K2Node_CallFunction":
            continue
        if "add or update blendable" not in node_title(node).lower():
            continue
        blend_pin = node.find_input_pin("InBlendableObject")
        weight_pin = node.find_input_pin("InWeight")
        if not blend_pin or not weight_pin:
            continue
        blend_val = unreal.BlueprintGraphPinLibrary.get_pin_value(blend_pin) or ""
        weight_val = unreal.BlueprintGraphPinLibrary.get_pin_value(weight_pin) or ""
        if "M_FishEyeLens_Inst" in blend_val and weight_val.startswith("0"):
            to_remove.append(node)

    if not to_remove:
        return

    editor.remove_nodes(to_remove)
    log(f"Removed {len(to_remove)} existing strip-lens nodes for re-wire")


def wire_strip_lens_on_begin_play(bp) -> None:
    event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)

    remove_existing_strip_nodes(editor)
    if strip_lens_already_wired(editor):
        log("Runtime strip lens nodes already present")
        return

    begin = editor.find_event_node("ReceiveBeginPlay")
    anchor = begin.get_node_pos() if begin else unreal.IntPoint(0, 0)
    strip_fish, strip_vign = create_strip_lens_chain(editor, anchor)

    hooked = False
    setup_macros = []
    for node in editor.list_all_nodes():
        if macro_is_begin_setup(node):
            setup_macros.append(node)

    for node in setup_macros:
        then_pin = node.find_then_pin()
        if not then_pin:
            continue
        downstream = unreal.BlueprintGraphPinLibrary.list_connected_pins(then_pin)
        if downstream:
            chain_exec_before(downstream[0], strip_fish.find_execute_pin(), strip_vign.find_then_pin())
        else:
            connect_exec(then_pin, strip_fish.find_execute_pin())
        hooked = True
        log(f"Hooked strip-lens chain after {node.get_name()}")

    if not hooked and begin:
        begin_then = begin.find_then_pin()
        existing = unreal.BlueprintGraphPinLibrary.list_connected_pins(begin_then)
        if existing:
            chain_exec_before(existing[0], strip_fish.find_execute_pin(), strip_vign.find_then_pin())
        else:
            connect_exec(begin_then, strip_fish.find_execute_pin())
        hooked = True
        log("Hooked strip-lens chain on ReceiveBeginPlay fallback")

    try:
        editor.add_comment_node(
            STRIP_MARKER,
            unreal.Vector2D(anchor.x + 240, anchor.y - 40),
            unreal.Vector2D(900, 320),
        )
    except Exception as exc:
        log(f"Skip comment node: {exc}")

    if hooked:
        log("Wired runtime strip for fisheye/vignette (weight 0)")
    else:
        log("Warning: could not find BeginSetup/BeginPlay hook; template strip still applied")


def remove_landscape_framing_nodes(bp) -> None:
    event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)
    to_remove = []

    for node in editor.list_all_nodes():
        cls = node.get_class().get_name()
        if cls != "K2Node_CallFunction":
            continue
        rot_pin = node.find_input_pin("NewRotation")
        if not rot_pin:
            continue
        val = unreal.BlueprintGraphPinLibrary.get_pin_value(rot_pin)
        if val and "Pitch=2.500000" in val:
            to_remove.append(node)

    for node in editor.list_all_nodes():
        if node.get_class().get_name() != "K2Node_ExecutionSequence":
            continue
        then0 = node.find_output_pin("then_0")
        if not then0:
            continue
        for linked in unreal.BlueprintGraphPinLibrary.list_connected_pins(then0):
            owner = unreal.BlueprintGraphPinLibrary.get_owning_node(linked)
            if owner and owner.get_class().get_name() == "K2Node_IfThenElse":
                stack = [owner]
                seen = set()
                while stack:
                    n = stack.pop()
                    if id(n) in seen:
                        continue
                    seen.add(id(n))
                    to_remove.append(n)
                    for pin in unreal.BlueprintEditorLibrary.list_all_pins(n):
                        if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) != unreal.EdGraphPinDirection.EGPD_INPUT:
                            continue
                        for linked_in in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                            src = unreal.BlueprintGraphPinLibrary.get_owning_node(linked_in)
                            if src and src.get_class().get_name() in (
                                "K2Node_CallFunction",
                                "K2Node_PromotableOperator",
                                "K2Node_VariableGet",
                            ):
                                stack.append(src)
                tick = editor.find_event_node("ReceiveTick")
                if tick:
                    for linked_tick in unreal.BlueprintGraphPinLibrary.list_connected_pins(tick.find_then_pin()):
                        if unreal.BlueprintGraphPinLibrary.get_owning_node(linked_tick) == node:
                            then1 = node.find_output_pin("then_1")
                            if then1:
                                for downstream in unreal.BlueprintGraphPinLibrary.list_connected_pins(then1):
                                    unreal.BlueprintGraphPinLibrary.break_pin_links(tick.find_then_pin())
                                    tick.find_then_pin().try_create_connection(downstream)
                to_remove.append(node)

    if not to_remove:
        log("No landscape framing nodes found to remove")
        return

    unique = []
    seen_ids = set()
    for node in to_remove:
        if id(node) in seen_ids:
            continue
        seen_ids.add(id(node))
        unique.append(node)

    editor.remove_nodes(unique)
    log(f"Removed {len(unique)} landscape framing nodes from EventGraph")


def configure_ar_session() -> None:
    config = unreal.load_asset(AR_SESSION)
    if not config:
        raise RuntimeError(f"Missing {AR_SESSION}")
    set_prop(config, ("bEnableAutomaticCameraOverlay",), True)
    set_prop(config, ("bEnableAutomaticCameraTracking",), False)
    unreal.EditorAssetLibrary.save_asset(AR_SESSION, only_if_is_dirty=False)
    log("AR overlay on, tracking off (FPS camera unchanged)")


def configure_map_ar() -> None:
    unreal.EditorLoadingAndSavingUtils.load_map(MAP_AR)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not world:
        raise RuntimeError("Editor world unavailable")
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PostProcessVolume.static_class()):
        set_prop(actor, ("unbound", "b_unbound"), True)
        configure_post_process_settings(actor.settings, actor.get_name())
        actor.settings = actor.settings
    unreal.EditorLoadingAndSavingUtils.save_current_level()
    log("Saved Map_AR post process")


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    bp = unreal.load_asset(BP_ASSET)
    if not bp:
        raise RuntimeError(f"Missing {BP_ASSET}")

    remove_landscape_framing_nodes(bp)
    configure_character_blueprint(bp)
    disable_bodycam_component_effects()
    disable_lens_materials()
    wire_strip_lens_in_begin_setup_macro(bp)
    wire_strip_lens_on_begin_play(bp)
    configure_ar_session()
    configure_map_ar()

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)
    log("Done - redeploy; outline kept, fisheye/vignette disabled, AR passthrough background-only")


main()
