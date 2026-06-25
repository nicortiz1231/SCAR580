"""Restore weapon visibility by reconnecting post-spawn exec chains."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_weapons_visibility.log")

CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
ITEM_BP = "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base"

# SetAmmo -> SpawnAttachments -> VariableGet -> Set ProceduralValues
SPAWN_CHAINS = (
    ("K2Node_CallFunction_140", "K2Node_VariableGet_133"),
    ("K2Node_CallFunction_141", "K2Node_VariableGet_83"),
)


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[fix_weapons] {msg}")


def connect_exec(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def find_node(editor, name):
    for node in editor.list_all_nodes():
        if node.get_name() == name:
            return node
    return None


def reconnect_spawn_chains(char_bp) -> None:
    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
    )

    for spawn_name, get_name in SPAWN_CHAINS:
        spawn_att = find_node(editor, spawn_name)
        var_get = find_node(editor, get_name)
        if not spawn_att or not var_get:
            log(f"SKIP missing {spawn_name} or {get_name}")
            continue

        then = spawn_att.find_output_pin("then")
        exec_in = var_get.find_input_pin("execute")
        if not then or not exec_in:
            log(f"SKIP missing pins on {spawn_name} / {get_name}")
            continue

        linked = list(unreal.BlueprintGraphPinLibrary.list_connected_pins(then))
        if linked:
            owners = [lp.get_owning_node().get_name() for lp in linked]
            if get_name in owners:
                log(f"{spawn_name} already connected to {get_name}")
                continue
            then.break_pin_links()

        if connect_exec(then, exec_in):
            log(f"Connected {spawn_name} -> {get_name}")
        else:
            log(f"FAILED connect {spawn_name} -> {get_name}")


def remove_orphan_character_scope_nodes(char_bp) -> None:
    """Remove leftover sniper-only scope nodes that may block exec flow."""
    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
    )
    remove = []
    for node in editor.list_all_nodes():
        cls = node.get_class().get_name()
        title = str(node.get_node_title())
        if "SM_4xScopeForSniper" in title:
            remove.append(node)
        if cls == "K2Node_CallFunction" and "EqualEqual" in title:
            remove.append(node)
        if cls == "K2Node_CallFunction" and "SetStaticMesh" in title:
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                if val and "SM_4xScopeForSniper" in val:
                    remove.append(node)
                    break
        if cls == "K2Node_IfThenElse":
            cond = node.find_input_pin("Condition")
            if not cond:
                continue
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(cond):
                owner = lp.get_owning_node()
                if owner in remove or "EqualEqual" in str(owner.get_node_title()):
                    remove.append(node)
                    break

    remove = list({id(n): n for n in remove}.values())
    if remove:
        editor.remove_nodes(remove)
        log(f"Removed {len(remove)} orphan character scope node(s)")


def fix_item_spawnattachments_else(item_bp) -> None:
    """Ensure item SpawnAttachments branch else completes (no stuck exec)."""
    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(item_bp)
    )
    spawn_event = None
    for node in editor.list_all_nodes():
        if node.get_class().get_name() != "K2Node_CustomEvent":
            continue
        if "SpawnAttachments" in str(node.get_node_title()):
            spawn_event = node
            break
    if not spawn_event:
        return

    branch = None
    then_pin = spawn_event.find_output_pin("then")
    if then_pin:
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then_pin):
            owner = lp.get_owning_node()
            if owner.get_class().get_name() == "K2Node_IfThenElse":
                branch = owner
                break

    if not branch:
        return

    else_pin = branch.find_output_pin("else")
    if else_pin and not list(unreal.BlueprintGraphPinLibrary.list_connected_pins(else_pin)):
        # Custom event: else can stay open; log only.
        log("Item SpawnAttachments branch else is open (OK for custom event)")


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    char_bp = unreal.load_asset(f"{CHAR_BP}.BP_FPCharacter")
    item_bp = unreal.load_asset(f"{ITEM_BP}.BP_Item_Base")
    if not char_bp:
        raise RuntimeError("BP_FPCharacter not found")

    remove_orphan_character_scope_nodes(char_bp)
    reconnect_spawn_chains(char_bp)

    if item_bp:
        fix_item_spawnattachments_else(item_bp)
        unreal.BlueprintEditorLibrary.compile_blueprint(item_bp)
        unreal.EditorAssetLibrary.save_asset(ITEM_BP, only_if_is_dirty=False)

    unreal.BlueprintEditorLibrary.compile_blueprint(char_bp)
    unreal.EditorAssetLibrary.save_asset(CHAR_BP, only_if_is_dirty=False)
    log("Done")


main()
