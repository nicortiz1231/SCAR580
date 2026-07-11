"""Wire portrait layout call after UI_Modding AddToViewport on BP_FPCharacter."""
import unreal
from pathlib import Path

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_modding_portrait_char.log")

APPLY_LAYOUT_FN = "/Script/SCAR.SCARWeaponAttachmentBlueprintLibrary:ApplyWeaponModdingPortraitLayout"
GET_PC_FN = "/Script/Engine.GameplayStatics:GetPlayerController"


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[fix_modding_portrait_char] {msg}")


def find_node(editor, name: str):
    for node in editor.list_all_nodes():
        if node.get_name() == name:
            return node
    return None


def connect_exec(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def connect_data(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def output_pin(node, preferred: str):
    pin = node.find_output_pin(preferred) if hasattr(node, "find_output_pin") else None
    if pin:
        return pin
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) == unreal.EdGraphPinDirection.EGPD_OUTPUT:
            return pin
    return None


def insert_exec_after_pin(exec_out_pin, new_node) -> bool:
    if not exec_out_pin or not new_node:
        return False
    downstream = []
    for pin in exec_out_pin.list_connected_pins():
        if pin.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT:
            downstream.append(pin)
    exec_in = new_node.find_input_pin("execute")
    exec_out = new_node.find_output_pin("then")
    if not exec_in or not exec_out:
        return False
    if downstream:
        exec_out_pin.break_pin_links()
        if not connect_exec(exec_out_pin, exec_in):
            return False
        for pin in downstream:
            connect_exec(exec_out, pin)
        return True
    return connect_exec(exec_out_pin, exec_in)


def already_patched(editor) -> bool:
    for node in editor.list_all_nodes():
        if "ApplyWeaponModdingPortraitLayout" in str(node.get_node_title()):
            return True
    return False


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    bp = unreal.load_asset(BP_ASSET)
    if not bp:
        raise RuntimeError(f"Missing {BP_ASSET}")

    eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)

    if already_patched(editor):
        log("Portrait layout call already wired — skipping")
        return

    add_viewport = find_node(editor, "K2Node_CallFunction_180")
    if not add_viewport:
        raise RuntimeError("Missing K2Node_CallFunction_180 AddToViewport")

    layout = editor.add_call_function_node(APPLY_LAYOUT_FN)
    get_ui = editor.add_get_member_variable_node("UI_Modding")
    if not layout or not get_ui:
        raise RuntimeError("Failed creating portrait layout nodes")

    if not insert_exec_after_pin(add_viewport.find_output_pin("then"), layout):
        raise RuntimeError("Failed inserting portrait layout into exec chain")

    # PlayerController from GetPlayerController(self, 0)
    connect_data(output_pin(get_ui, "UI_Modding"), layout.find_input_pin("ModdingWidget"))

    get_pc = editor.add_call_function_node(GET_PC_FN)
    if not get_pc:
        raise RuntimeError("Failed creating GetPlayerController node")
    get_pc.find_input_pin("PlayerIndex").set_pin_value("0")
    get_pc.find_input_pin("WorldContextObject").set_pin_value("self")
    connect_data(output_pin(get_pc, "ReturnValue"), layout.find_input_pin("PlayerController"))

    log("Wired ApplyWeaponModdingPortraitLayout after UI_Modding AddToViewport")

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)
    log("Saved BP_FPCharacter")


main()
