"""Fix BP_FPCharacter compile errors: connect OpticSight/ScopeSightMesh targets on spawn chain."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_char_scope_compile.log")
CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
ITEM_CLASS = "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base_C"
SNIPER_CLASS = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper_C"
SPAWNED_ITEM_GET = {
    "K2Node_CallFunction_140": "K2Node_VariableGet_133",
    "K2Node_CallFunction_141": "K2Node_VariableGet_83",
}


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[char_compile] {msg}")


def connect_data(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def connect_target(node, spawned_out) -> None:
    for pin_name in ("self", "Target"):
        pin = node.find_input_pin(pin_name)
        if pin:
            pin.break_pin_links()
            connect_data(spawned_out, pin)
            return


def find_node(editor, name):
    for node in editor.list_all_nodes():
        if node.get_name() == name:
            return node
    return None


def get_spawned_out(spawned_get):
    pin = spawned_get.find_output_pin("SpawnedItem")
    if pin:
        return pin
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(spawned_get):
        if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) == unreal.EdGraphPinDirection.EGPD_OUTPUT:
            return pin
    return None


def repair_all_scope_gets(char_bp) -> None:
    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
    )

    for spawn_name, spawned_get_name in SPAWNED_ITEM_GET.items():
        spawned_get = find_node(editor, spawned_get_name)
        if not spawned_get:
            log(f"SKIP missing {spawned_get_name}")
            continue
        spawned_out = get_spawned_out(spawned_get)
        if not spawned_out:
            continue

        spawn_att = find_node(editor, spawn_name)
        if not spawn_att:
            continue

        then = spawn_att.find_output_pin("then")
        visited = set()
        stack = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
            stack.append(lp.get_owning_node())
        while stack:
            node = stack.pop()
            if id(node) in visited:
                continue
            visited.add(id(node))
            title = str(node.get_node_title())
            cls = node.get_class().get_name()
            if cls == "K2Node_VariableGet" and ("OpticSight" in title or "ScopeSightMesh" in title):
                connect_target(node, spawned_out)
                log(f"Connected {node.get_name()} ({title}) to {spawned_get_name}")
            then_pin = node.find_output_pin("then")
            if then_pin:
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then_pin):
                    stack.append(lp.get_owning_node())
            if cls == "K2Node_IfThenElse":
                for branch in ("then", "else"):
                    pin = node.find_output_pin(branch)
                    if pin:
                        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                            stack.append(lp.get_owning_node())


def main() -> None:
    if LOG.exists():
        LOG.unlink()
    char_bp = unreal.load_asset(f"{CHAR_BP}.BP_FPCharacter")
    repair_all_scope_gets(char_bp)
    char_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(char_bp)
    unreal.EditorAssetLibrary.save_asset(CHAR_BP, only_if_is_dirty=False)
    log("Saved BP_FPCharacter after target repair")


main()
