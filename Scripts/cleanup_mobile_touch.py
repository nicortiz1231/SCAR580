"""Safely remove mobile touch wiring without deleting combat nodes."""
import unreal

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"

STOP_NAMES = {
    "K2Node_IfThenElse_50",
    "K2Node_IfThenElse_11",
    "K2Node_IfThenElse_3",
    "K2Node_IfThenElse_23",
    "K2Node_CallFunction_285",
    "K2Node_CallFunction_56",
    "K2Node_CallFunction_379",
    "K2Node_CallFunction_153",
    "K2Node_EnhancedInputAction_24",
    "K2Node_EnhancedInputAction_5",
    "K2Node_EnhancedInputAction_9",
    "K2Node_CustomEvent_16",
    "K2Node_CustomEvent_19",
}


def title(node) -> str:
    return str(node.get_node_title()).replace("\n", " | ")


def exec_out_nodes(node):
    if node.get_name() in STOP_NAMES:
        return []
    outs = []
    for pin_name in ("then", "else", "Completed", "Update"):
        pin = node.find_then_pin() if pin_name == "then" else node.find_output_pin(pin_name)
        if not pin:
            pin = node.find_else_pin() if pin_name == "else" else None
        if not pin:
            continue
        for linked in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            n = unreal.BlueprintGraphPinLibrary.get_owning_node(linked)
            if n and n.get_name() not in STOP_NAMES:
                outs.append(n)
    return outs


bp = unreal.load_asset(BP_ASSET)
eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)
remove = set()

for node in editor.list_all_nodes():
    cls = node.get_class().get_name()
    if cls == "K2Node_Comment":
        try:
            if "Mobile Touch Zones" in str(node.get_editor_property("node_comment")) or "Mobile Touch Zones v" in str(node.get_editor_property("node_comment")):
                remove.add(node)
        except Exception:
            pass
    if "GetInputTouchState" in title(node):
        remove.add(node)

tick = editor.find_event_node("ReceiveTick")
recoil = None
if tick:
    then = tick.find_then_pin()
    seq = None
    for linked in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
        n = unreal.BlueprintGraphPinLibrary.get_owning_node(linked)
        if n and "Sequence" in title(n):
            seq = n
            pin0 = n.find_output_pin("then_0")
            if pin0:
                for linked2 in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin0):
                    n2 = unreal.BlueprintGraphPinLibrary.get_owning_node(linked2)
                    if n2 and "Recoil" in title(n2):
                        recoil = n2
    if seq:
        remove.add(seq)
        pin1 = seq.find_output_pin("then_1")
        if pin1:
            stack = []
            for linked2 in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin1):
                n = unreal.BlueprintGraphPinLibrary.get_owning_node(linked2)
                if n and n.get_name() not in STOP_NAMES:
                    stack.append(n)
            while stack:
                n = stack.pop()
                if n in remove or n.get_name() in STOP_NAMES:
                    continue
                remove.add(n)
                stack.extend(exec_out_nodes(n))
    unreal.BlueprintGraphPinLibrary.break_pin_links(then)
    if recoil:
        then.try_create_connection(recoil.find_execute_pin())

if remove:
    editor.remove_nodes(list(remove))
    unreal.log(f"[cleanup] removed {len(remove)} nodes safely")

unreal.BlueprintEditorLibrary.compile_blueprint(bp)
unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)
unreal.log("[cleanup] done")
