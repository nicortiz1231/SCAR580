"""Sniper wheel: circular 4x scope (NewEnumerator7), not holo sight (HOLOSIGHT/Enumerator4)."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_sniper_pickup_look.log")
CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
ITEM_CLASS = "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base_C"
SCOPE_MESH = "/Game/BodycamFPSKIT/Demo/Meshes/SM_4xScopeForSniper.SM_4xScopeForSniper"
SET_MESH = "/Script/Engine.StaticMeshComponent:SetStaticMesh"
SET_VIS = "/Script/Engine.SceneComponent:SetVisibility"

# NewEnumerator7 = circular sniper scope mesh + ADS FOV on character/AutomaticBase switches.
# HOLOSIGHT (Enumerator1/4) = red-dot holo like assault rifle — wrong for sniper.
SNIPER_SCOPE_ATTACHMENTS = (
    "(Sight_37_688233D743AA415C91250EBC240B11ED=NewEnumerator7,"
    "Laser_38_3209213B48BBF0256E8473A33CC4C0FE=NewEnumerator0,"
    "Muzzle_42_288332C341D7A8B7E31632867A1FE4DB=NewEnumerator0,"
    "Grip_46_62A21AB489496DC33D1ACDA661CA2D84=NewEnumerator0)"
)

SPAWN_ATT = "K2Node_CallFunction_141"
DOWNSTREAM_GET = "K2Node_VariableGet_83"
SPAWNED_SET = "K2Node_VariableSet_15"


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[sniper_pickup_look] {msg}")


def find_node(editor, name):
    for node in editor.list_all_nodes():
        if node.get_name() == name:
            return node
    return None


def connect_exec(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def connect_data(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def connect_target(node, spawned_out) -> None:
    for pin_name in ("self", "Target"):
        pin = node.find_input_pin(pin_name)
        if pin:
            pin.break_pin_links()
            connect_data(spawned_out, pin)
            return


def output_pin(node, preferred=None):
    if preferred:
        p = node.find_output_pin(preferred)
        if p:
            return p
    for p in unreal.BlueprintEditorLibrary.list_all_pins(node):
        if unreal.BlueprintGraphPinLibrary.get_pin_direction(p) == unreal.EdGraphPinDirection.EGPD_OUTPUT:
            return p
    return None


def is_scope_apply_node(node) -> bool:
    if node.get_class().get_name() != "K2Node_CallFunction":
        return False
    title = str(node.get_node_title())
    if "SetStaticMesh" not in title:
        return False
    mesh_pin = node.find_input_pin("NewMesh")
    if not mesh_pin:
        return False
    val = str(unreal.BlueprintGraphPinLibrary.get_pin_value(mesh_pin))
    if "SM_4xScopeForSniper" in val:
        return True
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(mesh_pin):
        if "ScopeSightMesh" in str(lp.get_owning_node().get_node_title()):
            return True
    return False


def remove_existing_scope_nodes(editor) -> None:
    remove = []
    for node in editor.list_all_nodes():
        if is_scope_apply_node(node):
            remove.append(node)
        if node.get_class().get_name() == "K2Node_VariableGet" and "ScopeSightMesh" in str(node.get_node_title()):
            remove.append(node)
        if node.get_class().get_name() == "K2Node_CallFunction" and "SetVisibility" in str(node.get_node_title()):
            exec_pin = node.find_input_pin("execute")
            if exec_pin:
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(exec_pin):
                    if is_scope_apply_node(lp.get_owning_node()):
                        remove.append(node)
                        break
    if remove:
        editor.remove_nodes(list({id(n): n for n in remove}.values()))
        log(f"Removed {len(remove)} old scope-apply node(s)")


def set_hands_slot(char_bp) -> None:
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
                    pin.set_pin_value(SNIPER_SCOPE_ATTACHMENTS)
                    log(f"HandsSlot attachments -> {unreal.BlueprintGraphPinLibrary.get_pin_value(pin)}")
                elif pname.startswith("ItemData_AmmoCount"):
                    pin.set_pin_value("12")
                elif pname.startswith("ItemData_MaxAmmo"):
                    pin.set_pin_value("120")
            return
    log("WARN: HandsSlot node missing")


def insert_scope_after_spawnattachments(char_bp) -> None:
    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
    )

    spawn_att = find_node(editor, SPAWN_ATT)
    spawned_set = find_node(editor, SPAWNED_SET)
    downstream = find_node(editor, DOWNSTREAM_GET)
    if not spawn_att or not spawned_set or not downstream:
        raise RuntimeError("Missing spawn chain nodes for scope insert")

    spawned_out = output_pin(spawned_set, "Output_Get")
    if not spawned_out:
        raise RuntimeError("Missing SpawnedItem output")

    remove_existing_scope_nodes(editor)

    set_mesh = editor.add_call_function_node(SET_MESH)
    set_vis = editor.add_call_function_node(SET_VIS)
    get_optic = editor.add_get_member_variable_node("OpticSight", ITEM_CLASS)
    if not all((set_mesh, set_vis, get_optic)):
        raise RuntimeError("Failed creating scope apply nodes")

    connect_target(get_optic, spawned_out)
    connect_data(output_pin(get_optic, "OpticSight"), set_mesh.find_input_pin("self"))
    connect_data(output_pin(get_optic, "OpticSight"), set_vis.find_input_pin("self"))

    mesh_pin = set_mesh.find_input_pin("NewMesh")
    if mesh_pin:
        mesh_pin.break_pin_links()
        mesh_pin.set_pin_value(SCOPE_MESH)

    vis_pin = set_vis.find_input_pin("bNewVisibility")
    if vis_pin:
        vis_pin.set_pin_value("true")

    spawn_then = spawn_att.find_output_pin("then")
    downstream_exec = downstream.find_input_pin("execute")
    if not spawn_then or not downstream_exec:
        raise RuntimeError("Missing exec pins on spawn chain")

    spawn_then.break_pin_links()
    connect_exec(spawn_then, set_mesh.find_input_pin("execute"))
    connect_exec(set_mesh.find_output_pin("then"), set_vis.find_input_pin("execute"))
    connect_exec(set_vis.find_output_pin("then"), downstream_exec)
    log("Wired SpawnAttachments -> SetStaticMesh(SM_4xScopeForSniper) -> SetVisibility -> equip chain")


def verify_spawn_chain(char_bp) -> None:
    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
    )
    cur = find_node(editor, SPAWNED_SET)
    seen = set()
    for _ in range(15):
        if not cur:
            break
        name = cur.get_name()
        if name in seen:
            log(f"VERIFY LOOP at {name}")
            return
        seen.add(name)
        then = cur.find_output_pin("then")
        if not then:
            break
        links = [lp for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then) if lp.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT]
        if not links:
            log(f"VERIFY chain ends at {name}")
            return
        cur = links[0].get_owning_node()
    log(f"VERIFY chain nodes: {' -> '.join(seen)}")


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    char_bp = unreal.load_asset(f"{CHAR_BP}.BP_FPCharacter")
    if not char_bp:
        raise RuntimeError("Missing BP_FPCharacter")

    set_hands_slot(char_bp)
    insert_scope_after_spawnattachments(char_bp)

    char_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(char_bp)
    unreal.EditorAssetLibrary.save_asset(CHAR_BP, only_if_is_dirty=False)

    # Compile resets HandsSlot attachment pins — re-apply and save without recompile.
    set_hands_slot(char_bp)
    char_bp.modify()
    unreal.EditorAssetLibrary.save_asset(CHAR_BP, only_if_is_dirty=False)

    verify_spawn_chain(char_bp)
    log("Done")


main()
