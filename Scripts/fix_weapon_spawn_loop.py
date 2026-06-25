"""Break spawn exec loop and restore post-SpawnAttachments equip chain."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_weapon_spawn_loop.log")
CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"

# Correct order: Set SpawnedItem -> SetWeaponAmmoData -> SetAmmo -> SpawnAttachments -> VariableGet
SNIPER_CHAIN = (
    ("K2Node_VariableSet_15", "K2Node_CallFunction_157"),
    ("K2Node_CallFunction_157", "K2Node_CallFunction_212"),
    ("K2Node_CallFunction_212", "K2Node_CallFunction_141"),
    ("K2Node_CallFunction_141", "K2Node_VariableGet_83"),
)
PRIMARY_CHAIN = (
    ("K2Node_CallFunction_140", "K2Node_VariableGet_133"),
)

PICKUP_ATTACHMENTS = (
    "(Sight_37_688233D743AA415C91250EBC240B11ED=NewEnumerator1,"
    "Laser_38_3209213B48BBF0256E8473A33CC4C0FE=NewEnumerator1,"
    "Muzzle_42_288332C341D7A8B7E31632867A1FE4DB=NewEnumerator1,"
    "Grip_46_62A21AB489496DC33D1ACDA661CA2D84=NewEnumerator0)"
)


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[fix_spawn_loop] {msg}")


def find_node(editor, name):
    for node in editor.list_all_nodes():
        if node.get_name() == name:
            return node
    return None


def connect_exec(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def wire_chain(editor, pairs) -> None:
    for src_name, dst_name in pairs:
        src = find_node(editor, src_name)
        dst = find_node(editor, dst_name)
        if not src or not dst:
            log(f"SKIP missing {src_name} or {dst_name}")
            continue
        src_then = src.find_output_pin("then")
        dst_exec = dst.find_input_pin("execute")
        if not src_then or not dst_exec:
            log(f"SKIP missing pins {src_name}->{dst_name}")
            continue
        src_then.break_pin_links()
        dst_exec.break_pin_links()
        if connect_exec(src_then, dst_exec):
            log(f"Wired {src_name} -> {dst_name}")
        else:
            log(f"FAILED {src_name} -> {dst_name}")


def set_hands_slot_attachments(char_bp) -> None:
    for graph in unreal.BlueprintEditorLibrary.list_graphs(char_bp):
        if graph.get_name() != "BeginSetup":
            continue
        editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        for node in editor.list_all_nodes():
            if node.get_name() != "K2Node_GenericCreateObject_2":
                continue
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                if pname.startswith("ItemData_Attachments"):
                    pin.set_pin_value(PICKUP_ATTACHMENTS)
                    log(f"HandsSlot attachments -> pickup defaults")


def verify_no_loop(editor) -> None:
    start = find_node(editor, "K2Node_VariableSet_15")
    if not start:
        return
    then = start.find_output_pin("then")
    seen = set()
    node = start
    for _ in range(30):
        then = node.find_output_pin("then")
        if not then:
            break
        links = [lp for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then) if lp.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT]
        if not links:
            log(f"Chain ends at {node.get_name()} (OK)")
            return
        nxt = links[0].get_owning_node()
        if nxt.get_name() in seen:
            log(f"LOOP at {nxt.get_name()} — still broken")
            return
        seen.add(nxt.get_name())
        node = nxt
    log(f"Chain length OK ({len(seen)} nodes), no early loop")


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    char_bp = unreal.load_asset(f"{CHAR_BP}.BP_FPCharacter")
    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
    )

    # Break feedback: SpawnAttachments must not feed SetWeaponAmmoData.
    spawn_att = find_node(editor, "K2Node_CallFunction_141")
    set_ammo_data = find_node(editor, "K2Node_CallFunction_157")
    if spawn_att and set_ammo_data:
        spawn_then = spawn_att.find_output_pin("then")
        ammo_exec = set_ammo_data.find_input_pin("execute")
        if spawn_then and ammo_exec:
            for lp in list(unreal.BlueprintGraphPinLibrary.list_connected_pins(spawn_then)):
                if lp.get_owning_node() == set_ammo_data:
                    spawn_then.break_pin_links()
                    log("Broke SpawnAttachments -> SetWeaponAmmoData feedback loop")

    wire_chain(editor, SNIPER_CHAIN)
    wire_chain(editor, PRIMARY_CHAIN)
    set_hands_slot_attachments(char_bp)
    verify_no_loop(editor)

    char_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(char_bp)
    unreal.EditorAssetLibrary.save_asset(CHAR_BP, only_if_is_dirty=False)
    log("Done")


main()
