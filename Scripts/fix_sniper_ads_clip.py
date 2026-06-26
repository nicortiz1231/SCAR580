"""Remove redundant post-SpawnAttachments scope nodes; match Map_Test pickup equip chain."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_sniper_ads_clip.log")
CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
SCOPE_MESH = "SM_4xScopeForSniper"
SPAWN_ATT = "K2Node_CallFunction_141"
DOWNSTREAM_GET = "K2Node_VariableGet_83"


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[fix_sniper_ads_clip] {msg}")


def find_node(editor, name: str):
    for node in editor.list_all_nodes():
        if node.get_name() == name:
            return node
    return None


def connect_exec(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def is_scope_fixup_node(node) -> bool:
    if node.get_class().get_name() != "K2Node_CallFunction":
        return False
    title = str(node.get_node_title())
    if "SetStaticMesh" in title:
        mesh_pin = node.find_input_pin("NewMesh")
        if mesh_pin:
            val = str(unreal.BlueprintGraphPinLibrary.get_pin_value(mesh_pin))
            if SCOPE_MESH in val:
                return True
    if "SetVisibility" in title:
        exec_pin = node.find_input_pin("execute")
        if exec_pin:
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(exec_pin):
                prev = lp.get_owning_node()
                if prev.get_class().get_name() == "K2Node_CallFunction" and "SetStaticMesh" in str(
                    prev.get_node_title()
                ):
                    mesh_pin = prev.find_input_pin("NewMesh")
                    if mesh_pin and SCOPE_MESH in str(
                        unreal.BlueprintGraphPinLibrary.get_pin_value(mesh_pin)
                    ):
                        return True
    return False


def reconnect_spawn_to_downstream(editor) -> None:
    spawn_att = find_node(editor, SPAWN_ATT)
    downstream = find_node(editor, DOWNSTREAM_GET)
    if not spawn_att or not downstream:
        raise RuntimeError("Missing SpawnAttachments or downstream VariableGet")

    scope_nodes = [n for n in editor.list_all_nodes() if is_scope_fixup_node(n)]
    if not scope_nodes:
        spawn_then = spawn_att.find_output_pin("then")
        downstream_exec = downstream.find_input_pin("execute")
        if spawn_then and downstream_exec:
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(spawn_then):
                if lp.get_owning_node().get_name() == DOWNSTREAM_GET:
                    log("Spawn chain already matches pickup parity")
                    return
        log("No scope fixup nodes found; rewiring SpawnAttachments -> downstream")
    else:
        editor.remove_nodes(scope_nodes)
        log(f"Removed {len(scope_nodes)} redundant scope fixup node(s)")

    spawn_then = spawn_att.find_output_pin("then")
    downstream_exec = downstream.find_input_pin("execute")
    if not spawn_then or not downstream_exec:
        raise RuntimeError("Missing exec pins")
    spawn_then.break_pin_links()
    connect_exec(spawn_then, downstream_exec)
    log("Rewired SpawnAttachments -> VariableGet_83 (pickup parity)")


def verify_chain(editor) -> None:
    spawn_att = find_node(editor, SPAWN_ATT)
    if not spawn_att:
        return
    cur = spawn_att
    chain = []
    for _ in range(12):
        chain.append(cur.get_name())
        then = cur.find_output_pin("then")
        if not then:
            break
        links = [
            lp
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then)
            if lp.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT
        ]
        if not links:
            break
        cur = links[0].get_owning_node()
    log(f"VERIFY spawn chain: {' -> '.join(chain)}")


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    char_bp = unreal.load_asset(f"{CHAR_BP}.BP_FPCharacter")
    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
    )

    reconnect_spawn_to_downstream(editor)
    verify_chain(editor)

    char_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(char_bp)
    unreal.EditorAssetLibrary.save_asset(CHAR_BP, only_if_is_dirty=False)
    log("Done")


main()
