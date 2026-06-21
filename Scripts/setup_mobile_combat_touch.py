"""Remove tick touch zones; restore IA_Shoot; activate TI_MobileCombat on BeginPlay."""
import unreal
from pathlib import Path

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
TI_PATH = "/Game/SCAR580/Input/TI_MobileCombat.TI_MobileCombat"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/setup_mobile_combat_touch.log")
MARKER = "Mobile Combat TouchInterface"
IA_SHOOT_NODE = "K2Node_EnhancedInputAction_24"
SHOOT_BRANCH = "K2Node_IfThenElse_50"

TOUCH_MARKERS = (
    "Mobile Touch Zones v",
    "Mobile Suppress LMB Shoot",
    "Mobile Combat TouchInterface",
)


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[setup_mobile_combat] {msg}")


def title(node) -> str:
    return str(node.get_node_title()).replace("\n", " | ")


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


def is_marker_comment(node) -> bool:
    if node.get_class().get_name() != "K2Node_Comment":
        return False
    try:
        text = str(node.get_editor_property("node_comment"))
    except Exception:
        return False
    return any(m in text for m in TOUCH_MARKERS)


def find_node(editor, name: str):
    for node in editor.list_all_nodes():
        if node.get_name() == name:
            return node
    return None


def cleanup_tick_touch(editor) -> None:
    stop = {
        SHOOT_BRANCH,
        "K2Node_IfThenElse_11",
        "K2Node_CallFunction_285",
        "K2Node_CallFunction_56",
        "K2Node_CallFunction_379",
        "K2Node_CallFunction_153",
        IA_SHOOT_NODE,
        "K2Node_CallFunction_86",
        "K2Node_CallFunction_61",
    }
    remove = set()
    for node in editor.list_all_nodes():
        if is_marker_comment(node):
            remove.add(node)
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
            stack = []
            pin1 = seq.find_output_pin("then_1")
            if pin1:
                for linked2 in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin1):
                    n = unreal.BlueprintGraphPinLibrary.get_owning_node(linked2)
                    if n and n.get_name() not in stop:
                        stack.append(n)
            while stack:
                n = stack.pop()
                if n in remove or n.get_name() in stop:
                    continue
                remove.add(n)
                cls = n.get_class().get_name()
                pins = []
                then_pin = n.find_then_pin()
                if then_pin:
                    pins.append(then_pin)
                if cls == "K2Node_IfThenElse":
                    else_pin = n.find_else_pin()
                    if else_pin:
                        pins.append(else_pin)
                for pin in pins:
                    for linked2 in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                        n2 = unreal.BlueprintGraphPinLibrary.get_owning_node(linked2)
                        if n2 and n2.get_name() not in stop and n2 not in remove:
                            stack.append(n2)
        unreal.BlueprintGraphPinLibrary.break_pin_links(then)
        if recoil:
            then.try_create_connection(recoil.find_execute_pin())

    if remove:
        editor.remove_nodes(list(remove))
        log(f"Removed {len(remove)} tick-touch / suppress nodes")


def cleanup_suppress_near_ia_shoot(editor) -> None:
    ia = find_node(editor, IA_SHOOT_NODE)
    if not ia:
        return
    started = ia.find_output_pin("Started")
    if not started:
        return
    remove = set()
    for linked in unreal.BlueprintGraphPinLibrary.list_connected_pins(started):
        n = unreal.BlueprintGraphPinLibrary.get_owning_node(linked)
        if not n or n.get_name() == SHOOT_BRANCH:
            continue
        if n.get_class().get_name() == "K2Node_IfThenElse":
            remove.add(n)
            stack = [n]
            while stack:
                cur = stack.pop()
                remove.add(cur)
                for pin in (cur.find_then_pin(), cur.find_else_pin()):
                    if not pin:
                        continue
                    for l2 in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                        n2 = unreal.BlueprintGraphPinLibrary.get_owning_node(l2)
                        if n2 and n2.get_name() not in (SHOOT_BRANCH, IA_SHOOT_NODE):
                            stack.append(n2)
        if "GetInputTouchState" in title(n):
            remove.add(n)
    if remove:
        unreal.BlueprintGraphPinLibrary.break_pin_links(started)
        editor.remove_nodes(list(remove))
        log(f"Removed {len(remove)} IA_Shoot suppress nodes")


def restore_ia_shoot(editor) -> None:
    ia = find_node(editor, IA_SHOOT_NODE)
    shoot_branch = find_node(editor, SHOOT_BRANCH)
    if not ia or not shoot_branch:
        raise RuntimeError("Missing IA_Shoot or shoot branch")
    started = ia.find_output_pin("Started")
    shoot_exec = shoot_branch.find_execute_pin()
    links = unreal.BlueprintGraphPinLibrary.list_connected_pins(started)
    for linked in links:
        n = unreal.BlueprintGraphPinLibrary.get_owning_node(linked)
        if n and n.get_name() == SHOOT_BRANCH:
            log("IA_Shoot Started already wired to shoot branch")
            return
    unreal.BlueprintGraphPinLibrary.break_pin_links(started)
    connect_exec(started, shoot_exec)
    log("Reconnected IA_Shoot Started -> shoot branch (TouchInterface LMB only)")


def already_wired(editor) -> bool:
    for node in editor.list_all_nodes():
        if is_marker_comment(node):
            try:
                if MARKER in str(node.get_editor_property("node_comment")):
                    return True
            except Exception:
                pass
    return False


def wire_activate_touch_interface(editor) -> None:
    if already_wired(editor):
        log("TouchInterface BeginPlay hook already present")
        return

    ti = unreal.load_asset(TI_PATH)
    if not ti:
        raise RuntimeError(f"Missing {TI_PATH}")

    begin = editor.find_event_node("ReceiveBeginPlay")
    if not begin:
        raise RuntimeError("ReceiveBeginPlay missing")

    get_pc = editor.add_call_function_node("/Script/Engine.GameplayStatics.GetPlayerController")
    activate = editor.add_call_function_node("/Script/Engine.PlayerController.ActivateTouchInterface")
    if not get_pc or not activate:
        raise RuntimeError("Could not create ActivateTouchInterface nodes")

    pin_value = lambda pin, val: pin and pin.set_pin_value(val)
    pin_value(get_pc.find_input_pin("PlayerIndex"), "0")
    pin_value(get_pc.find_input_pin("WorldContextObject"), "self")

    ti_pin = activate.find_input_pin("NewTouchInterface") or activate.find_input_pin("TouchInterface")
    if ti_pin:
        ti_pin.set_pin_value(str(ti.get_path_name()))
    connect_data(get_pc.find_output_pin("ReturnValue"), activate.find_input_pin("self"))

    begin_pos = begin.get_node_pos()
    seq = editor.create_node_from_name(
        "Utilities|FlowControl|Sequence",
        unreal.Vector2D(begin_pos.x + 200, begin_pos.y + 400),
        [],
    )
    if not seq:
        raise RuntimeError("Could not create BeginPlay Sequence")

    begin_then = begin.find_then_pin()
    begin_links = unreal.BlueprintGraphPinLibrary.list_connected_pins(begin_then)
    unreal.BlueprintGraphPinLibrary.break_pin_links(begin_then)
    connect_exec(begin_then, seq.find_execute_pin())
    if begin_links:
        connect_exec(seq.find_output_pin("then_0"), begin_links[0])
    connect_exec(seq.find_output_pin("then_1"), activate.find_execute_pin())

    editor.add_comment_node(
        MARKER,
        unreal.Vector2D(begin_pos.x + 180, begin_pos.y + 380),
        unreal.Vector2D(720, 280),
    )
    log("Wired BeginPlay -> ActivateTouchInterface(TI_MobileCombat)")


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()
    bp = unreal.load_asset(BP_ASSET)
    if not bp:
        raise RuntimeError(f"Missing {BP_ASSET}")
    eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)
    cleanup_tick_touch(editor)
    cleanup_suppress_near_ia_shoot(editor)
    restore_ia_shoot(editor)
    wire_activate_touch_interface(editor)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)
    log("Done")


main()
