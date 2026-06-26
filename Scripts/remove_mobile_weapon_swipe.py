"""Remove mobile weapon swipe wiring from BP_FPCharacter."""
import unreal
from pathlib import Path

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/remove_mobile_weapon_swipe.log")

MARKERS = (
    "Mobile Weapon Swipe v2",
    "Mobile Weapon Swipe v1",
    "Mobile Weapon Swipe",
)

STOP = {
    "K2Node_CallFunction_279",
    "K2Node_CallFunction_248",
    "K2Node_CallFunction_153",
    "K2Node_ExecutionSequence_9",
    "K2Node_IfThenElse_4",
    "K2Node_IfThenElse_32",
    "K2Node_Event_4",
}


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[remove_weapon_swipe] {msg}")


def is_marker(node) -> bool:
    if node.get_class().get_name() != "K2Node_Comment":
        return False
    try:
        text = str(node.get_editor_property("node_comment"))
    except Exception:
        return False
    return any(m in text for m in MARKERS)


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()
    bp = unreal.load_asset(BP_ASSET)
    if not bp:
        raise RuntimeError(f"Missing {BP_ASSET}")
    event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)

    remove = set()
    for node in editor.list_all_nodes():
        if is_marker(node):
            remove.add(node)

    if not remove:
        log("No weapon swipe marker found")
        return

    stack = list(remove)
    while stack:
        node = stack.pop()
        if node.get_name() in STOP:
            continue
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) != unreal.EdGraphPinDirection.EGPD_INPUT:
                continue
            for linked in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                owner = unreal.BlueprintGraphPinLibrary.get_owning_node(linked)
                if owner and owner not in remove and owner.get_name() not in STOP:
                    cls = owner.get_class().get_name()
                    if cls in (
                        "K2Node_CallFunction",
                        "K2Node_IfThenElse",
                        "K2Node_VariableGet",
                        "K2Node_VariableSet",
                        "EdGraphNode_Comment",
                    ):
                        remove.add(owner)
                        stack.append(owner)

    # Disconnect parallel tick slot if sequence remains.
    seq = None
    for node in editor.list_all_nodes():
        if node.get_name() == "K2Node_ExecutionSequence_9":
            seq = node
            break
    if seq:
        pin = seq.find_output_pin("then_1")
        if pin:
            unreal.BlueprintGraphPinLibrary.break_pin_links(pin)

    if remove:
        editor.remove_nodes(list(remove))
        log(f"Removed {len(remove)} weapon-swipe nodes")

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)
    log("Done")


main()
