"""Block IA_Shoot (LeftMouseButton) on mobile — touch zones drive BeginFire instead."""
import unreal
from pathlib import Path

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_mobile_suppress_lmb_shoot.log")
MARKER = "Mobile Suppress LMB Shoot"
IA_SHOOT_NODE = "K2Node_EnhancedInputAction_24"
SHOOT_BRANCH = "K2Node_IfThenElse_50"


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[suppress_lmb] {msg}")


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


def already_wired(editor) -> bool:
    for node in editor.list_all_nodes():
        if node.get_class().get_name() != "K2Node_Comment":
            continue
        try:
            if MARKER in str(node.get_editor_property("node_comment")):
                return True
        except Exception:
            pass
    return False


def find_node(editor, name: str):
    for node in editor.list_all_nodes():
        if node.get_name() == name:
            return node
    return None


def find_ia_shoot(editor):
    node = find_node(editor, IA_SHOOT_NODE)
    if node:
        return node
    for n in editor.list_all_nodes():
        if n.get_class().get_name() != "K2Node_EnhancedInputAction":
            continue
        if "IA_Shoot" in title(n):
            return n
    return None


def wire_suppress(bp) -> None:
    event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)
    if already_wired(editor):
        log("Already wired")
        return

    ia_shoot = find_ia_shoot(editor)
    shoot_branch = find_node(editor, SHOOT_BRANCH)
    if not ia_shoot or not shoot_branch:
        raise RuntimeError("Missing IA_Shoot or shoot branch")

    started = ia_shoot.find_output_pin("Started")
    if not started:
        raise RuntimeError("IA_Shoot Started pin missing")

    shoot_exec = shoot_branch.find_execute_pin()
    links = unreal.BlueprintGraphPinLibrary.list_connected_pins(started)
    if not links:
        log("IA_Shoot Started has no outgoing exec — checking direct shoot branch exec sources")
    else:
        for linked in links:
            pin = linked
            n = unreal.BlueprintGraphPinLibrary.get_owning_node(linked)
            if n and n.get_name() == shoot_branch.get_name():
                unreal.BlueprintGraphPinLibrary.break_pin_links(started)
                log("Broke IA_Shoot Started -> IfThenElse_50")
                break
        else:
            # Started may route through an intermediate node (Sequence, etc.)
            for linked in links:
                n = unreal.BlueprintGraphPinLibrary.get_owning_node(linked)
                log(f"IA_Shoot Started -> {n.get_name() if n else '?'}")
            unreal.BlueprintGraphPinLibrary.break_pin_links(started)
            log("Broke all IA_Shoot Started exec links")

    # iOS routes primary touch through LeftMouseButton -> IA_Shoot. Block that path whenever
    # a finger is down; mobile touch zones call BeginFire/StopFire directly instead.
    get_pc = editor.add_call_function_node("/Script/Engine.GameplayStatics.GetPlayerController")
    get_touch = editor.add_call_function_node("/Script/Engine.PlayerController.GetInputTouchState")
    if not get_pc or not get_touch:
        raise RuntimeError("Could not create touch probe nodes")

    pin_value = lambda pin, val: pin and pin.set_pin_value(val)
    pin_value(get_pc.find_input_pin("PlayerIndex"), "0")
    pin_value(get_pc.find_input_pin("WorldContextObject"), "self")
    pin_value(get_touch.find_input_pin("FingerIndex"), "0")
    connect_data(get_pc.find_output_pin("ReturnValue"), get_touch.find_input_pin("self"))

    branch = editor.add_branch_node()
    if not branch:
        raise RuntimeError("Could not create suppress branch")

    connect_data(get_touch.find_output_pin("bIsCurrentlyPressed"), branch.find_input_pin("Condition"))
    connect_exec(started, branch.find_execute_pin())
    connect_exec(branch.find_else_pin(), shoot_exec)

    pos = ia_shoot.get_node_pos()
    editor.add_comment_node(
        MARKER,
        unreal.Vector2D(pos.x + 40, pos.y + 120),
        unreal.Vector2D(520, 220),
    )
    log("Wired: IA_Shoot Started blocked while finger 0 is down (touch zones own combat)")


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()
    bp = unreal.load_asset(BP_ASSET)
    if not bp:
        raise RuntimeError(f"Missing {BP_ASSET}")
    wire_suppress(bp)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)
    log("Done")


main()
