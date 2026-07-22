"""Create K2Node_SpawnActorFromClass via NewObject, then wire BeginPlay."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_horror_kit_zombies.log")
SPAWN_BP = "/Game/FirstPersonHorrorKit/Blueprints/Enemy/BP_EnemySpawn"
ENEMY_BP = "/Game/FirstPersonHorrorKit/Blueprints/Enemy/BP_Enemy"
ENEMY_CLASS_PATH = "/Game/FirstPersonHorrorKit/Blueprints/Enemy/BP_Enemy.BP_Enemy_C"
GET_XFORM_FN = "/Script/Engine.Actor:GetActorTransform"


def log(msg: str) -> None:
    prev = OUT.read_text() if OUT.exists() else ""
    OUT.write_text(prev + str(msg) + "\n")
    unreal.log(f"[fix_horror_zombies] {msg}")
    print(msg)


def connect(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def break_all(pin) -> None:
    if pin:
        pin.break_pin_links()


def output_pin(node, preferred: str):
    pin = node.find_output_pin(preferred) if hasattr(node, "find_output_pin") else None
    if pin:
        return pin
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) == unreal.EdGraphPinDirection.EGPD_OUTPUT:
            if str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin)) == preferred:
                return pin
    return None


def create_spawn_node(graph):
    # Prefer existing
    eg = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    for node in eg.list_all_nodes():
        if node.get_class().get_name() == "K2Node_SpawnActorFromClass":
            return node

    cls = getattr(unreal, "K2Node_SpawnActorFromClass", None)
    log(f"K2Node_SpawnActorFromClass type={cls}")
    if cls is None:
        raise RuntimeError("K2Node_SpawnActorFromClass not exposed to Python")

    node = unreal.new_object(cls, graph)
    node.node_pos_x = 480
    node.node_pos_y = 0
    graph.add_node(node, True, False)
    try:
        node.allocate_default_pins()
    except Exception as exc:
        log(f"allocate_default_pins: {exc}")
    try:
        node.reconstruct_node()
    except Exception as exc:
        log(f"reconstruct_node: {exc}")
    try:
        node.post_placed_new_node()
    except Exception as exc:
        log(f"post_placed_new_node: {exc}")
    log(f"Created raw SpawnActor node {node.get_name()}")
    return node


def main():
    if OUT.exists():
        OUT.unlink()
    log("=== Fix Horror Kit zombies ===")

    enemy_bp = unreal.load_asset(f"{ENEMY_BP}.BP_Enemy")
    spawn_bp = unreal.load_asset(f"{SPAWN_BP}.BP_EnemySpawn")
    enemy_class = enemy_bp.generated_class()

    cdo = unreal.get_default_object(enemy_class)
    for prop, value in (("CanAttack?", True), ("Bone", "spine_01"), ("bone", "spine_01")):
        try:
            cdo.set_editor_property(prop, value)
            log(f"CDO {prop}={value}")
        except Exception:
            pass
    unreal.BlueprintEditorLibrary.compile_blueprint(enemy_bp)
    unreal.EditorAssetLibrary.save_asset(ENEMY_BP, only_if_is_dirty=False)

    graph = unreal.BlueprintEditorLibrary.find_event_graph(spawn_bp)
    eg = unreal.BlueprintGraphEditor.get_graph_editor(graph)

    begin = next(
        n for n in eg.list_all_nodes()
        if n.get_class().get_name() == "K2Node_Event" and "BeginPlay" in str(n.get_node_title())
    )

    spawn = create_spawn_node(graph)
    # refresh editor view of nodes
    eg = unreal.BlueprintGraphEditor.get_graph_editor(graph)

    class_pin = spawn.find_input_pin("Class") if hasattr(spawn, "find_input_pin") else None
    if not class_pin:
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(spawn):
            if str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin)) == "Class":
                class_pin = pin
                break
    if class_pin:
        for path in (ENEMY_CLASS_PATH, enemy_class.get_path_name()):
            try:
                class_pin.set_pin_value(path)
                log(f"Class={unreal.BlueprintGraphPinLibrary.get_pin_value(class_pin)!r}")
                break
            except Exception as exc:
                log(f"Class set failed {path}: {exc}")
    try:
        spawn.set_editor_property("node_class", enemy_class)
        log("node_class set")
    except Exception as exc:
        log(f"node_class skipped: {exc}")

    get_xform = None
    for node in eg.list_all_nodes():
        if "GetActorTransform" in str(node.get_node_title()).replace("\n", ""):
            get_xform = node
            break
    if not get_xform:
        get_xform = eg.add_call_function_node(GET_XFORM_FN)
        log(f"Added GetActorTransform {get_xform.get_name() if get_xform else None}")

    begin_then = begin.find_output_pin("then")
    spawn_exec = spawn.find_input_pin("execute") if hasattr(spawn, "find_input_pin") else None
    if not spawn_exec:
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(spawn):
            if str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin)) == "execute":
                spawn_exec = pin
                break
    break_all(begin_then)
    break_all(spawn_exec)
    log(f"BeginPlay->Spawn={connect(begin_then, spawn_exec)}")

    if get_xform:
        xform_out = output_pin(get_xform, "ReturnValue")
        spawn_xform = spawn.find_input_pin("SpawnTransform") if hasattr(spawn, "find_input_pin") else None
        if not spawn_xform:
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(spawn):
                if str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin)) == "SpawnTransform":
                    spawn_xform = pin
                    break
        break_all(spawn_xform)
        log(f"Transform={connect(xform_out, spawn_xform)}")

    coll = spawn.find_input_pin("CollisionHandlingOverride") if hasattr(spawn, "find_input_pin") else None
    if coll:
        try:
            coll.set_pin_value("AlwaysSpawn")
            log("AlwaysSpawn")
        except Exception as exc:
            log(f"AlwaysSpawn skipped: {exc}")

    spawn_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(spawn_bp)
    unreal.EditorAssetLibrary.save_asset(SPAWN_BP, only_if_is_dirty=False)
    log("Saved BP_EnemySpawn")

    # Soften cast
    enemy_eg = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(enemy_bp)
    )
    for node in enemy_eg.list_all_nodes():
        if "Cast To BP_FirstPersonCharacter" in str(node.get_node_title()):
            src = unreal.load_object(
                None,
                "/Game/FirstPersonHorrorKit/Blueprints/Player/BP_FirstPersonCharacter.BP_FirstPersonCharacter_C",
            )
            try:
                ok = enemy_eg.retarget_node_class(node, src, unreal.Character.static_class())
                log(f"Cast softened={ok}")
                unreal.BlueprintEditorLibrary.compile_blueprint(enemy_bp)
                unreal.EditorAssetLibrary.save_asset(ENEMY_BP, only_if_is_dirty=False)
            except Exception as exc:
                log(f"Cast soften failed: {exc}")
            break

    eg2 = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(spawn_bp)
    )
    for node in eg2.list_all_nodes():
        log(f"NODE {node.get_name()} | {node.get_class().get_name()} | {str(node.get_node_title()).replace(chr(10),' ')}")
    log("Done")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log(f"FATAL: {exc}")
        raise
