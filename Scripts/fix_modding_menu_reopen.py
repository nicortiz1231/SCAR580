"""Wire RefreshEquippedWeaponAttachments after modding UI SpawnAttachments chain."""
import unreal
from pathlib import Path

WBP_PATH = "/Game/BodycamFPSKIT/Blueprints/Widgets/UI_WeaponModding"
WBP_ASSET = f"{WBP_PATH}.UI_WeaponModding"
LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_modding_menu_reopen.log")
REFRESH_FN = "/Script/SCAR.SCARWeaponAttachmentBlueprintLibrary:RefreshEquippedWeaponAttachments"
GET_OWNING_FN = "/Script/UMG.Widget:GetOwningPlayer"
GET_PAWN_FN = "/Script/Engine.Controller:K2_GetPawn"


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[fix_modding_menu_reopen] {msg}")


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


def wire_apply_after(editor, anchor) -> None:
    for node in editor.list_all_nodes():
        title = str(node.get_node_title())
        if "RefreshEquippedWeaponAttachments" in title or "ApplySpawnedWeaponAttachments" in title:
            log("ApplySpawnedWeaponAttachments already present")
            return

    apply_node = editor.add_call_function_node(REFRESH_FN)
    get_owning = editor.add_call_function_node(GET_OWNING_FN)
    get_pawn = editor.add_call_function_node(GET_PAWN_FN)
    self_nodes = [n for n in editor.list_all_nodes() if n.get_class().get_name() == "K2Node_Self"]
    if not self_nodes:
        raise RuntimeError("No Self node found in UI_WeaponModding EventGraph")
    self_node = self_nodes[0]
    if not apply_node:
        raise RuntimeError(f"Failed creating apply node for {REFRESH_FN}")
    if not get_owning:
        raise RuntimeError("Failed creating GetOwningPlayer node")
    if not get_pawn:
        raise RuntimeError("Failed creating K2_GetPawn node")

    if not insert_exec_after_pin(anchor.find_output_pin("then"), apply_node):
        raise RuntimeError(f"Failed wiring exec after {anchor.get_name()}")

    connect_data(output_pin(self_node, "self"), get_owning.find_input_pin("self"))
    connect_data(output_pin(get_owning, "ReturnValue"), get_pawn.find_input_pin("self"))
    connect_data(output_pin(get_pawn, "ReturnValue"), apply_node.find_input_pin("Pawn"))
    log(f"Wired RefreshEquippedWeaponAttachments after {anchor.get_name()}")


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    wbp = unreal.load_asset(WBP_ASSET)
    eg = unreal.BlueprintEditorLibrary.find_event_graph(wbp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)

    anchors = []
    for node in editor.list_all_nodes():
        title = str(node.get_node_title())
        if "EnsureWeaponLaserFlashEffects" in title or title == "SpawnAttachments":
            anchors.append(node)

    if not anchors:
        raise RuntimeError("No SpawnAttachments / Ensure anchors found")

    wire_apply_after(editor, anchors[-1])

    unreal.BlueprintEditorLibrary.compile_blueprint(wbp)
    unreal.EditorAssetLibrary.save_asset(WBP_PATH, only_if_is_dirty=False)
    log("Saved UI_WeaponModding")


main()
