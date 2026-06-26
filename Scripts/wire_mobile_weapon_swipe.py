"""Attach SCARMobileWeaponSwipeComponent and remove legacy blueprint tick swipe."""
import unreal
from pathlib import Path

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
COMPONENT_CLASS = "/Script/SCAR.SCARMobileWeaponSwipeComponent"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/wire_mobile_weapon_swipe.log")

OLD_MARKERS = (
    "Mobile Weapon Swipe v4",
    "Mobile Weapon Swipe v3",
    "Mobile Weapon Swipe v2",
    "Mobile Weapon Swipe v1",
    "Mobile Weapon Swipe",
)


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[weapon_swipe] {msg}")


def title(node) -> str:
    return str(node.get_node_title()).replace("\n", " | ")


def comment_text(node) -> str:
    try:
        return str(node.get_editor_property("node_comment"))
    except Exception:
        return ""


def is_marker_comment(node) -> bool:
    if node.get_class().get_name() != "K2Node_Comment":
        return False
    return any(m in comment_text(node) for m in OLD_MARKERS)


def blueprint_has_component(bp, class_name_substring: str) -> bool:
    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = subsystem.k2_gather_subobject_data_for_blueprint(bp)
    for handle in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
        if obj and class_name_substring in obj.get_class().get_name():
            return True
    return False


def cleanup_blueprint_swipe(editor) -> None:
    remove = set()
    for node in editor.list_all_nodes():
        if is_marker_comment(node):
            remove.add(node)
        if "WeaponSwipe" in title(node):
            remove.add(node)

    stop = {
        "K2Node_CallFunction_279",
        "K2Node_CallFunction_248",
        "K2Node_ExecutionSequence_9",
        "K2Node_CallFunction_153",
        "K2Node_IfThenElse_4",
        "K2Node_IfThenElse_32",
    }
    stack = list(remove)
    while stack:
        node = stack.pop()
        if node.get_name() in stop:
            continue
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) != unreal.EdGraphPinDirection.EGPD_INPUT:
                continue
            for linked in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                owner = unreal.BlueprintGraphPinLibrary.get_owning_node(linked)
                if owner and owner not in remove and owner.get_name() not in stop:
                    if owner.get_class().get_name() in (
                        "K2Node_CallFunction",
                        "K2Node_IfThenElse",
                        "K2Node_VariableGet",
                        "K2Node_VariableSet",
                        "EdGraphNode_Comment",
                    ):
                        remove.add(owner)
                        stack.append(owner)

    for node in editor.list_all_nodes():
        if node.get_name() == "K2Node_ExecutionSequence_9":
            pin = node.find_output_pin("then_1")
            if pin:
                unreal.BlueprintGraphPinLibrary.break_pin_links(pin)

    if remove:
        editor.remove_nodes(list(remove))
        log(f"Removed {len(remove)} legacy blueprint weapon-swipe nodes")


def ensure_swipe_component(bp) -> None:
    component_class = unreal.load_class(None, COMPONENT_CLASS)
    if not component_class:
        raise RuntimeError(
            "SCARMobileWeaponSwipeComponent not compiled yet — build SCAR module first"
        )

    if blueprint_has_component(bp, "SCARMobileWeaponSwipe"):
        log("BP_FPCharacter already has SCARMobileWeaponSwipe component")
        return

    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = subsystem.k2_gather_subobject_data_for_blueprint(bp)
    root_handle = handles[0] if handles else None
    if not root_handle:
        raise RuntimeError("Could not resolve BP_FPCharacter root subobject")

    params = unreal.AddNewSubobjectParams()
    params.parent_handle = root_handle
    params.new_class = component_class
    params.blueprint_context = bp

    result, fail_reason = subsystem.add_new_subobject(params)
    if fail_reason and str(fail_reason).strip():
        raise RuntimeError(f"Failed to add SCARMobileWeaponSwipeComponent: {fail_reason}")

    subsystem.rename_subobject(result, "SCARMobileWeaponSwipe")
    log("Added SCARMobileWeaponSwipeComponent to BP_FPCharacter")


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    bp = unreal.load_asset(BP_ASSET)
    if not bp:
        raise RuntimeError(f"Missing {BP_ASSET}")

    event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)
    cleanup_blueprint_swipe(editor)
    ensure_swipe_component(bp)

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)
    log("Done — C++ swipe component handles portrait/landscape weapon swipes")


main()
