"""Wire AR body combat hit markers into BP_FPCharacter and BP_Item_Base."""

import unreal
from pathlib import Path

LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/setup_ar_body_combat.log")

BP_FP_CHARACTER = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ITEM_BASE = "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base"
COMBAT_COMPONENT_CLASS = "/Script/SCAR.SCARBodyCombatComponent"
TRY_AR_SHOT_FN = (
    "/Script/SCAR.SCARBodyCombatBlueprintLibrary:"
    "TryApplyARBodyShot"
)


def connect_data(src, dst) -> bool:
    if src and dst:
        return bool(src.try_create_connection(dst))
    return False


def connect_exec(src, dst) -> bool:
    if src and dst:
        return bool(src.try_create_connection(dst))
    return False


def find_function_entry(editor):
    for node in editor.list_all_nodes():
        if node.get_class().get_name() == "K2Node_FunctionEntry":
            return node
    return None


def insert_exec_after_pin(exec_out_pin, new_node):
    if not exec_out_pin or not new_node:
        return False

    downstream_exec_inputs = []
    try:
        for pin in exec_out_pin.list_connected_pins():
            if pin.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT:
                downstream_exec_inputs.append(pin)
    except Exception:
        pass

    exec_in = new_node.find_input_pin("execute")
    exec_out = new_node.find_output_pin("then")
    if not exec_in or not exec_out:
        return False

    if downstream_exec_inputs:
        exec_out_pin.break_pin_links()
        if not connect_exec(exec_out_pin, exec_in):
            return False
        for downstream in downstream_exec_inputs:
            connect_exec(exec_out, downstream)
        return True

    return connect_exec(exec_out_pin, exec_in)


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[setup_ar_body_combat] {msg}")


def blueprint_has_component(bp, class_name_substring: str) -> bool:
    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = subsystem.k2_gather_subobject_data_for_blueprint(bp)
    for handle in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
        if obj and class_name_substring in obj.get_class().get_name():
            return True
    return False


def ensure_combat_component_on_character() -> None:
    bp = unreal.load_asset(f"{BP_FP_CHARACTER}.BP_FPCharacter")
    if not bp:
        raise RuntimeError(f"Missing {BP_FP_CHARACTER}")

    component_class = unreal.load_class(None, COMBAT_COMPONENT_CLASS)
    if not component_class:
        log("SCARBodyCombatComponent not compiled yet; re-run after C++ build")
        return

    if blueprint_has_component(bp, "SCARBodyCombat"):
        log("BP_FPCharacter already has SCARBodyCombat component")
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
        raise RuntimeError(f"Failed to add SCARBodyCombatComponent: {fail_reason}")

    subsystem.rename_subobject(result, "SCARBodyCombat")
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_FP_CHARACTER, only_if_is_dirty=False)
    log("Added SCARBodyCombatComponent to BP_FPCharacter")


def node_title(node) -> str:
    try:
        return str(node.get_node_title(unreal.NodeTitleType.FULL_TITLE)).replace("\n", " | ")
    except Exception:
        return node.get_name()


def find_graph(bp, graph_name: str):
    for graph in unreal.BlueprintEditorLibrary.list_graphs(bp):
        if graph.get_name() == graph_name:
            return graph
    return None


def wire_item_base_ar_shot() -> None:
    bp = unreal.load_asset(f"{BP_ITEM_BASE}.BP_Item_Base")
    if not bp:
        raise RuntimeError(f"Missing {BP_ITEM_BASE}")

    graph = find_graph(bp, "Fire_HitScan")
    if not graph:
        log("Fire_HitScan graph not found on BP_Item_Base; manual wiring required")
        return

    editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    for node in editor.list_all_nodes():
        title = node_title(node)
        if "TryApplyARBodyShot" in title:
            log("BP_Item_Base Fire_HitScan already wired for AR body shots")
            return

    entry = find_function_entry(editor)
    if not entry:
        log("Fire_HitScan missing function entry; manual wiring required")
        return

    ar_shot_node = editor.add_call_function_node(TRY_AR_SHOT_FN)
    if not ar_shot_node:
        raise RuntimeError("Failed to create TryApplyARBodyShot node")

    base_damage_pin = ar_shot_node.find_input_pin("BaseDamage")
    crit_pin = ar_shot_node.find_input_pin("CriticalMultiplier")

    damage_get = editor.add_get_member_variable_node("Damage")
    if damage_get and base_damage_pin:
        connect_data(damage_get.find_output_pin("Damage"), base_damage_pin)
    elif base_damage_pin:
        base_damage_pin.set_pin_value("25.0")

    if crit_pin:
        crit_pin.set_pin_value("2.0")

    entry_then = entry.find_output_pin("then")
    if not insert_exec_after_pin(entry_then, ar_shot_node):
        log("Could not insert TryApplyARBodyShot into Fire_HitScan execution flow")
        editor.remove_nodes([ar_shot_node])
        return

    entry_pos = entry.get_node_pos()
    ar_shot_node.set_node_pos(unreal.IntPoint(entry_pos.x + 320, entry_pos.y + 220))
    log("Wired BP_Item_Base Fire_HitScan -> TryApplyARBodyShot")

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_ITEM_BASE, only_if_is_dirty=False)


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    ensure_combat_component_on_character()
    wire_item_base_ar_shot()
    log("AR body combat setup complete")


main()
