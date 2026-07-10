"""Wire BP_FPCharacter BeginPlay -> ShowARMultiplayerMenu for SCAR-580."""

import unreal
from pathlib import Path

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
SHOW_MENU_FN = "/Script/SCAR.SCARARMultiplayerBlueprintLibrary:ShowARMultiplayerMenu"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/setup_ar_multiplayer_menu_wire.log")
MARKER = "SCAR AR Multiplayer Menu"


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[setup_ar_multiplayer_menu_wire] {msg}")


def connect_exec(src, dst) -> None:
    if not src or not dst:
        raise RuntimeError("Missing exec pin")
    if not src.try_create_connection(dst):
        raise RuntimeError("Exec connection failed")


def cleanup_previous_menu_nodes(editor) -> None:
    remove_nodes = []
    for node in editor.list_all_nodes():
        if node.get_class().get_name() == "K2Node_Comment":
            try:
                if MARKER in str(node.get_editor_property("node_comment")):
                    remove_nodes.append(node)
            except Exception:
                pass
            continue

        if node.get_class().get_name() != "K2Node_CallFunction":
            continue

        for prop in ("function_reference", "FunctionReference"):
            try:
                fn_ref = str(node.get_editor_property(prop))
            except Exception:
                continue
            if "ShowARMultiplayerMenu" in fn_ref:
                remove_nodes.append(node)
                break

    for node in remove_nodes:
        editor.remove_node(node)
    if remove_nodes:
        log(f"Removed {len(remove_nodes)} previous multiplayer menu node(s)")


def wire_show_menu(editor) -> None:
    cleanup_previous_menu_nodes(editor)

    begin = editor.find_event_node("ReceiveBeginPlay")
    if not begin:
        raise RuntimeError("ReceiveBeginPlay missing on BP_FPCharacter")

    show_menu = editor.add_call_function_node(SHOW_MENU_FN)
    if not show_menu:
        raise RuntimeError(f"Could not create node for {SHOW_MENU_FN}")

    for pin_name in ("WorldContextObject", "__WorldContext"):
        world_pin = show_menu.find_input_pin(pin_name)
        if world_pin:
            world_pin.set_pin_value("self")
            break

    begin_pos = begin.get_node_pos()
    begin_then = begin.find_then_pin()
    begin_links = list(unreal.BlueprintGraphPinLibrary.list_connected_pins(begin_then))

    if begin_links:
        seq = editor.create_node_from_name(
            "Utilities|FlowControl|Sequence",
            unreal.Vector2D(begin_pos.x + 220, begin_pos.y + 520),
            [],
        )
        if not seq:
            raise RuntimeError("Could not create BeginPlay Sequence")
        unreal.BlueprintGraphPinLibrary.break_pin_links(begin_then)
        connect_exec(begin_then, seq.find_execute_pin())
        connect_exec(seq.find_output_pin("then_0"), begin_links[0])
        connect_exec(seq.find_output_pin("then_1"), show_menu.find_execute_pin())
    else:
        connect_exec(begin_then, show_menu.find_execute_pin())

    show_menu.set_node_pos(unreal.IntPoint(begin_pos.x + 220, begin_pos.y + 520))
    editor.add_comment_node(
        MARKER,
        unreal.Vector2D(begin_pos.x + 200, begin_pos.y + 500),
        unreal.Vector2D(640, 220),
    )
    log("Wired ReceiveBeginPlay -> ShowARMultiplayerMenu")


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    bp = unreal.load_asset(BP_ASSET)
    if not bp:
        raise RuntimeError(f"Missing {BP_ASSET}")

    event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)
    wire_show_menu(editor)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)
    log("Done — Play Map_AR in SCAR-580; menu should appear on character spawn.")


main()
