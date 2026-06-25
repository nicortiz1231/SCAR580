"""Remove broken sniper scope branch on BP_FPCharacter and wire a direct SetStaticMesh chain."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_char_scope_direct.log")
CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
ITEM_CLASS = "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base_C"
SCOPE_MESH = "/Game/BodycamFPSKIT/Demo/Meshes/SM_4xScopeForSniper.SM_4xScopeForSniper"
SET_MESH = "/Script/Engine.StaticMeshComponent:SetStaticMesh"
SET_VIS = "/Script/Engine.SceneComponent:SetVisibility"
SPAWN_PATHS = {
    "K2Node_CallFunction_140": "K2Node_VariableGet_133",
    "K2Node_CallFunction_141": "K2Node_VariableGet_83",
}


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[char_scope_direct] {msg}")


def connect_exec(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def connect_data(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def output_pin(node, preferred=None):
    if preferred:
        pin = node.find_output_pin(preferred)
        if pin:
            return pin
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) == unreal.EdGraphPinDirection.EGPD_OUTPUT:
            return pin
    return None


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
    return output_pin(spawned_get)


def pin_value_has_scope(pin) -> bool:
    try:
        val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
        return bool(val and "SM_4xScopeForSniper" in val)
    except Exception:
        return False


def is_scope_exec_node(node) -> bool:
    cls = node.get_class().get_name()
    title = str(node.get_node_title())
    if cls == "K2Node_IfThenElse":
        return True
    if cls == "K2Node_CallFunction" and "EqualEqual" in title:
        return True
    if cls == "K2Node_VariableGet" and "ScopeSightMesh" in title:
        return True
    if cls == "K2Node_CallFunction" and "SetStaticMesh" in title:
        mesh_pin = node.find_input_pin("NewMesh")
        return mesh_pin and pin_value_has_scope(mesh_pin)
    if cls == "K2Node_CallFunction" and "SetVisibility" in title:
        # Only treat as scope node if fed by a scope SetStaticMesh in the same local chain.
        exec_pin = node.find_input_pin("execute")
        if not exec_pin:
            return False
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(exec_pin):
            owner = lp.get_owning_node()
            if owner.get_class().get_name() == "K2Node_CallFunction" and "SetStaticMesh" in str(owner.get_node_title()):
                mesh_pin = owner.find_input_pin("NewMesh")
                if mesh_pin and pin_value_has_scope(mesh_pin):
                    return True
    return False


def collect_scope_subgraph(start_exec_pin):
    """Walk exec chain from start pin and collect scope-specific nodes plus final downstream exec input pin."""
    remove = []
    downstream = None
    current = start_exec_pin
    visited = set()

    while current:
        owners = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(current):
            if lp.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT:
                owners.append(lp)

        if len(owners) != 1:
            break

        node = owners[0].get_owning_node()
        if id(node) in visited:
            break
        visited.add(id(node))

        if node.get_class().get_name() == "K2Node_IfThenElse":
            remove.append(node)
            else_pin = node.find_output_pin("else")
            then_pin = node.find_output_pin("then")
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(else_pin):
                if lp.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT:
                    downstream = lp
            current = then_pin
            continue

        if is_scope_exec_node(node):
            remove.append(node)
            then_pin = node.find_output_pin("then")
            if then_pin:
                next_inputs = [
                    lp
                    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then_pin)
                    if lp.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT
                ]
                if len(next_inputs) == 1 and not is_scope_exec_node(next_inputs[0].get_owning_node()):
                    downstream = next_inputs[0]
                    break
                current = then_pin
                continue
            break

        break

    # Also collect data-only nodes feeding removed branch/equal nodes.
    extra = []
    for node in remove:
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) != unreal.EdGraphPinDirection.EGPD_INPUT:
                continue
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                owner = lp.get_owning_node()
                if owner in remove:
                    continue
                if owner.get_class().get_name() == "K2Node_VariableGet":
                    title = str(owner.get_node_title())
                    if "ScopeSightMesh" in title or "OpticSight" in title:
                        extra.append(owner)
    remove.extend(extra)
    return remove, downstream


def wire_direct_scope(editor, spawn_att, spawned_get) -> None:
    spawn_name = spawn_att.get_name()
    spawned_out = get_spawned_out(spawned_get)
    if not spawned_out:
        log(f"SKIP {spawn_name}: no SpawnedItem pin")
        return

    then_pin = spawn_att.find_output_pin("then")
    if not then_pin:
        log(f"SKIP {spawn_name}: no then pin")
        return

    remove, downstream = collect_scope_subgraph(then_pin)
    if remove:
        editor.remove_nodes(remove)
        log(f"Removed {len(remove)} broken scope nodes after {spawn_name}")
    else:
        # Capture existing downstream before we rewire.
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then_pin):
            if lp.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT:
                downstream = lp

    then_pin.break_pin_links()

    set_mesh = editor.add_call_function_node(SET_MESH)
    set_vis = editor.add_call_function_node(SET_VIS)
    get_optic = editor.add_get_member_variable_node("OpticSight", ITEM_CLASS)
    if not all((set_mesh, set_vis, get_optic)):
        raise RuntimeError(f"Failed creating scope nodes for {spawn_name}")

    connect_target(get_optic, spawned_out)
    optic_out = output_pin(get_optic, "OpticSight")
    connect_data(optic_out, set_mesh.find_input_pin("self"))
    connect_data(optic_out, set_vis.find_input_pin("self"))

    mesh_pin = set_mesh.find_input_pin("NewMesh")
    if mesh_pin:
        mesh_pin.break_pin_links()
        mesh_pin.set_pin_value(SCOPE_MESH)

    vis_pin = set_vis.find_input_pin("bNewVisibility")
    if vis_pin:
        vis_pin.set_pin_value("true")

    connect_exec(then_pin, set_mesh.find_input_pin("execute"))
    connect_exec(set_mesh.find_output_pin("then"), set_vis.find_input_pin("execute"))
    if downstream:
        connect_exec(set_vis.find_output_pin("then"), downstream)
    log(f"Wired {spawn_name} -> SetStaticMesh(SM_4xScopeForSniper) -> SetVisibility -> downstream")


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    char_bp = unreal.load_asset(f"{CHAR_BP}.BP_FPCharacter")
    if not char_bp:
        raise RuntimeError("Missing BP_FPCharacter")

    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
    )

    for spawn_name, spawned_get_name in SPAWN_PATHS.items():
        spawn_att = find_node(editor, spawn_name)
        spawned_get = find_node(editor, spawned_get_name)
        if not spawn_att or not spawned_get:
            log(f"SKIP missing nodes for {spawn_name}")
            continue
        wire_direct_scope(editor, spawn_att, spawned_get)

    char_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(char_bp)
    unreal.EditorAssetLibrary.save_asset(CHAR_BP, only_if_is_dirty=False)
    log("Saved BP_FPCharacter with direct sniper scope chain")


main()
