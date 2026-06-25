"""Replace empty-hands fallback spawn with sniper and wire Begin Setup on spawn."""
import unreal
from pathlib import Path

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
SNIPER_CLASS = (
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/"
    "BP_Weapon_Sniper.BP_Weapon_Sniper_C"
)
EMPTY_HANDS_CLASS = (
    "/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/"
    "BP_Weapon_EmptyHands.BP_Weapon_EmptyHands_C"
)
FALLBACK_SPAWN_NODE = "K2Node_SpawnActorFromClass_1"
HANDS_CONSTRUCT_NODE = "K2Node_GenericCreateObject_2"
BEGIN_SETUP_MACRO = "K2Node_MacroInstance_7"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/wire_sniper_wheel_slot.log")


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[sniper_wheel] {msg}")


def find_node(editor, name: str):
    for node in editor.list_all_nodes():
        if node.get_name() == name:
            return node
    return None


def find_weapon_data_pin(node):
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        if pname.startswith("ItemData_WeaponData"):
            return pin
    return None


def set_class_pin(node, class_path: str, label: str) -> None:
    class_pin = node.find_input_pin("Class")
    if not class_pin:
        raise RuntimeError(f"{label}: missing Class pin")
    before = unreal.BlueprintGraphPinLibrary.get_pin_value(class_pin)
    if before == class_path:
        log(f"{label} already {class_path}")
        return
    if not class_pin.set_pin_value(class_path):
        raise RuntimeError(f"{label}: failed to set Class pin to {class_path}")
    after = unreal.BlueprintGraphPinLibrary.get_pin_value(class_pin)
    if after != class_path:
        raise RuntimeError(f"{label}: Class pin stuck at {after!r}")
    log(f"{label} Class: {before!r} -> {after!r}")


def set_hands_construct_weapon_data(node, class_path: str) -> None:
    weapon_pin = find_weapon_data_pin(node)
    if not weapon_pin:
        raise RuntimeError("HandsSlot construct: missing WeaponData pin")
    before = unreal.BlueprintGraphPinLibrary.get_pin_value(weapon_pin)
    if before == class_path:
        log(f"HandsSlot construct already {class_path}")
        return
    if not weapon_pin.set_pin_value(class_path):
        raise RuntimeError(f"Failed to set HandsSlot WeaponData to {class_path}")
    after = unreal.BlueprintGraphPinLibrary.get_pin_value(weapon_pin)
    if after != class_path:
        raise RuntimeError(f"HandsSlot WeaponData stuck at {after!r}")
    log(f"HandsSlot construct WeaponData: {before!r} -> {after!r}")


def replace_empty_hands_class_refs(editor) -> None:
    """Update hard-coded EmptyHands class comparisons to sniper."""
    for node in editor.list_all_nodes():
        if node.get_class().get_name() != "K2Node_PromotableOperator":
            continue
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if pname != "B":
                continue
            try:
                val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            except Exception:
                val = ""
            if val != EMPTY_HANDS_CLASS:
                continue
            if not pin.set_pin_value(SNIPER_CLASS):
                raise RuntimeError(f"Failed to update {node.get_name()} EmptyHands compare")
            log(f"{node.get_name()} compare class: {EMPTY_HANDS_CLASS!r} -> {SNIPER_CLASS!r}")


def wire_begin_setup_on_begin_play(editor) -> None:
    begin_setup = find_node(editor, BEGIN_SETUP_MACRO)
    if not begin_setup:
        raise RuntimeError(f"Missing {BEGIN_SETUP_MACRO}")

    # Already wired?
    exec_pin = begin_setup.find_input_pin("execute")
    if exec_pin:
        for _ in unreal.BlueprintGraphPinLibrary.list_connected_pins(exec_pin):
            log("Begin Setup already wired on BeginPlay")
            return

    begin = editor.find_event_node("ReceiveBeginPlay")
    if not begin:
        raise RuntimeError("Missing ReceiveBeginPlay")

    # Insert Begin Setup at the start of the existing BeginPlay chain.
    first_then = begin.find_then_pin()
    if not first_then:
        raise RuntimeError("BeginPlay has no then pin")

    downstream_exec = None
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(first_then):
        downstream_exec = lp
        break

    if downstream_exec:
        unreal.BlueprintGraphPinLibrary.break_pin_links(first_then)

    if not first_then.try_create_connection(exec_pin):
        raise RuntimeError("Failed to connect BeginPlay -> Begin Setup")

    setup_then = begin_setup.find_then_pin()
    if not setup_then:
        raise RuntimeError("Begin Setup has no then pin")

    if downstream_exec:
        if not setup_then.try_create_connection(downstream_exec):
            raise RuntimeError("Failed to connect Begin Setup -> previous BeginPlay chain")

    log("Wired ReceiveBeginPlay -> Begin Setup -> existing startup chain")


def apply_sniper_wheel_fix(bp) -> None:
    event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    event_editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)

    fallback_spawn = find_node(event_editor, FALLBACK_SPAWN_NODE)
    if not fallback_spawn:
        raise RuntimeError(f"Missing {FALLBACK_SPAWN_NODE}")
    set_class_pin(fallback_spawn, SNIPER_CLASS, "Hands fallback spawn")
    replace_empty_hands_class_refs(event_editor)
    wire_begin_setup_on_begin_play(event_editor)

    begin_graph = None
    for graph in unreal.BlueprintEditorLibrary.list_graphs(bp):
        if graph.get_name() == "BeginSetup":
            begin_graph = graph
            break
    if begin_graph:
        begin_editor = unreal.BlueprintGraphEditor.get_graph_editor(begin_graph)
        construct = find_node(begin_editor, HANDS_CONSTRUCT_NODE)
        if construct:
            set_hands_construct_weapon_data(construct, SNIPER_CLASS)


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    bp = unreal.load_asset(BP_ASSET)
    if not bp:
        raise RuntimeError(f"Missing {BP_ASSET}")

    apply_sniper_wheel_fix(bp)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)
    log("Done — hands wheel slot spawns BP_Weapon_Sniper")


main()
