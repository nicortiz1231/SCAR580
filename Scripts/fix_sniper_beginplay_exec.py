"""Fix sniper BeginPlay exec + rename CustomEvent to SpawnAttachments override."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_sniper_beginplay_exec.log")
SNIPER_BP = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper"
SET_STATIC_MESH_FN = "/Script/Engine.StaticMeshComponent:SetStaticMesh"
SET_VISIBILITY_FN = "/Script/Engine.SceneComponent:SetVisibility"


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[beginplay_exec] {msg}")


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


def break_all(pin) -> None:
    if pin:
        pin.break_pin_links()


def fix_beginplay_scope(sniper_bp) -> None:
    eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(sniper_bp))
    nodes = {n.get_name(): n for n in eg.list_all_nodes()}

    # Remove misnamed custom event nodes
    remove = []
    for node in eg.list_all_nodes():
        if node.get_class().get_name() != "K2Node_CustomEvent":
            continue
        title = str(node.get_node_title()).replace("\n", " ")
        if title in ("CustomEvent", "CustomEvent_0") or title.startswith("CustomEvent"):
            remove.append(node)
    if remove:
        eg.remove_nodes(remove)
        log(f"Removed {len(remove)} misnamed custom event(s)")
        nodes = {n.get_name(): n for n in eg.list_all_nodes()}

    begin = nodes.get("K2Node_Event_0")
    parent = nodes.get("K2Node_CallParentFunction_0")
    if not begin or not parent:
        raise RuntimeError("Missing BeginPlay nodes")

    set_mesh = nodes.get("K2Node_CallFunction_0")
    set_vis = nodes.get("K2Node_CallFunction_1")
    get_optic = nodes.get("K2Node_VariableGet_0")
    get_scope = nodes.get("K2Node_VariableGet_1")

    if not set_mesh:
        set_mesh = eg.add_call_function_node(SET_STATIC_MESH_FN)
    if not set_vis:
        set_vis = eg.add_call_function_node(SET_VISIBILITY_FN)
    if not get_optic:
        get_optic = eg.add_get_member_variable_node("OpticSight")
    if not get_scope:
        get_scope = eg.add_get_member_variable_node("ScopeSightMesh")

    connect_data(output_pin(get_optic, "OpticSight"), set_mesh.find_input_pin("self"))
    connect_data(output_pin(get_scope, "ScopeSightMesh"), set_mesh.find_input_pin("NewMesh"))
    connect_data(output_pin(get_optic, "OpticSight"), set_vis.find_input_pin("self"))
    vis_pin = set_vis.find_input_pin("bNewVisibility")
    if vis_pin:
        vis_pin.set_pin_value("true")

    # Correct exec: BeginPlay -> Parent.execute; Parent.then -> SetMesh.execute -> SetVis.execute
    break_all(begin.find_output_pin("then"))
    break_all(begin.find_output_pin("execute"))
    break_all(parent.find_input_pin("execute"))
    break_all(parent.find_output_pin("then"))
    break_all(set_mesh.find_input_pin("execute"))
    break_all(set_mesh.find_output_pin("then"))
    break_all(set_vis.find_input_pin("execute"))

    connect_exec(begin.find_output_pin("then"), parent.find_input_pin("execute"))
    connect_exec(parent.find_output_pin("then"), set_mesh.find_input_pin("execute"))
    connect_exec(set_mesh.find_output_pin("then"), set_vis.find_input_pin("execute"))
    log("Fixed BeginPlay -> Parent -> SetStaticMesh(ScopeSightMesh) -> SetVisibility")


def add_spawnattachments_override(sniper_bp) -> None:
    """Child override: duplicate parent SpawnAttachments wiring on sniper graph."""
    eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(sniper_bp))

    for node in eg.list_all_nodes():
        if node.get_class().get_name() != "K2Node_CustomEvent":
            continue
        if "SpawnAttachments" in str(node.get_node_title()):
            then = node.find_output_pin("then")
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
                if "SetStaticMesh" in str(lp.get_owning_node().get_node_title()):
                    log("SpawnAttachments override already present")
                    return

    # Try creating override via BlueprintEditorLibrary if available
    try:
        spawn_event = eg.add_override_event_node("SpawnAttachments")
    except Exception:
        spawn_event = None
    if not spawn_event:
        spawn_event = eg.add_custom_event_node("SpawnAttachments")

    if spawn_event:
        for prop in ("CustomFunctionName", "custom_function_name", "EventName"):
            try:
                spawn_event.set_editor_property(prop, "SpawnAttachments")
            except Exception:
                pass
        title = str(spawn_event.get_node_title())
        log(f"SpawnAttachments event: {spawn_event.get_name()} title={title}")

        set_mesh = eg.add_call_function_node(SET_STATIC_MESH_FN)
        set_vis = eg.add_call_function_node(SET_VISIBILITY_FN)
        get_optic = eg.add_get_member_variable_node("OpticSight")
        get_scope = eg.add_get_member_variable_node("ScopeSightMesh")
        connect_data(output_pin(get_optic, "OpticSight"), set_mesh.find_input_pin("self"))
        connect_data(output_pin(get_scope, "ScopeSightMesh"), set_mesh.find_input_pin("NewMesh"))
        connect_data(output_pin(get_optic, "OpticSight"), set_vis.find_input_pin("self"))
        vis_pin = set_vis.find_input_pin("bNewVisibility")
        if vis_pin:
            vis_pin.set_pin_value("true")
        connect_exec(spawn_event.find_output_pin("then"), set_mesh.find_input_pin("execute"))
        connect_exec(set_mesh.find_output_pin("then"), set_vis.find_input_pin("execute"))
        log("Wired SpawnAttachments override")
    else:
        log("WARN: could not add SpawnAttachments override; BeginPlay handles scope")


def main() -> None:
    if LOG.exists():
        LOG.unlink()
    sniper_bp = unreal.load_asset(f"{SNIPER_BP}.BP_Weapon_Sniper")
    fix_beginplay_scope(sniper_bp)
    add_spawnattachments_override(sniper_bp)
    sniper_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(sniper_bp)
    unreal.EditorAssetLibrary.save_asset(SNIPER_BP, only_if_is_dirty=False)
    log("Done")


main()
