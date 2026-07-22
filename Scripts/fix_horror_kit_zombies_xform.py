"""Wire GetActorTransform into BP_EnemySpawn SpawnActor node."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_horror_kit_zombies_xform.log")
SPAWN_BP = "/Game/FirstPersonHorrorKit/Blueprints/Enemy/BP_EnemySpawn"
GET_XFORM_FN = "/Script/Engine.Actor:GetActorTransform"
GET_XFORM_FN2 = "/Script/Engine.Actor:GetTransform"


def log(msg: str) -> None:
    prev = OUT.read_text() if OUT.exists() else ""
    OUT.write_text(prev + str(msg) + "\n")
    unreal.log(f"[fix_horror_xform] {msg}")
    print(msg)


def connect(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def break_all(pin) -> None:
    if pin:
        pin.break_pin_links()


def pin_by_name(node, name, direction=None):
    if hasattr(node, "find_input_pin") and direction != unreal.EdGraphPinDirection.EGPD_OUTPUT:
        p = node.find_input_pin(name)
        if p:
            return p
    if hasattr(node, "find_output_pin") and direction != unreal.EdGraphPinDirection.EGPD_INPUT:
        p = node.find_output_pin(name)
        if p:
            return p
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        if str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin)) != name:
            continue
        if direction is None:
            return pin
        if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) == direction:
            return pin
    return None


def main():
    if OUT.exists():
        OUT.unlink()
    bp = unreal.load_asset(f"{SPAWN_BP}.BP_EnemySpawn")
    graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    eg = unreal.BlueprintGraphEditor.get_graph_editor(graph)

    begin = spawn = get_xform = None
    for node in eg.list_all_nodes():
        cls = node.get_class().get_name()
        title = str(node.get_node_title()).replace("\n", " ")
        log(f"NODE {node.get_name()} | {cls} | {title}")
        if cls == "K2Node_Event" and "BeginPlay" in title:
            begin = node
        elif cls == "K2Node_SpawnActorFromClass":
            spawn = node
        elif "GetActorTransform" in title.replace(" ", "") or "Get Transform" in title:
            get_xform = node

    if not begin or not spawn:
        raise RuntimeError(f"Missing nodes begin={begin} spawn={spawn}")

    if not get_xform:
        for fn in (GET_XFORM_FN, GET_XFORM_FN2, "/Script/Engine.Actor:K2_GetActorLocation"):
            try:
                get_xform = eg.add_call_function_node(fn)
                log(f"add_call_function_node({fn}) -> {get_xform}")
                if get_xform:
                    break
            except Exception as exc:
                log(f"add_call_function_node({fn}) ERR {exc}")

    if not get_xform:
        # Try create_node_from_name for GetActorTransform
        pins = list(unreal.BlueprintEditorLibrary.list_all_pins(begin))
        avail = [str(x) for x in list(eg.list_available_nodes([]) or [])]
        matches = [s for s in avail if "getactortransform" in s.lower().replace(" ", "")]
        log(f"GetActorTransform matches={matches[:20]}")
        if matches:
            get_xform = eg.create_node_from_name(matches[0], unreal.Vector2D(200.0, 80.0), pins)
            log(f"Created via name: {get_xform}")

    if not get_xform:
        raise RuntimeError("Could not create GetActorTransform")

    # Ensure BeginPlay -> Spawn
    begin_then = pin_by_name(begin, "then", unreal.EdGraphPinDirection.EGPD_OUTPUT)
    spawn_exec = pin_by_name(spawn, "execute", unreal.EdGraphPinDirection.EGPD_INPUT)
    break_all(begin_then)
    break_all(spawn_exec)
    log(f"BeginPlay->Spawn={connect(begin_then, spawn_exec)}")

    # Wire transform
    xform_out = pin_by_name(get_xform, "ReturnValue", unreal.EdGraphPinDirection.EGPD_OUTPUT)
    spawn_xform = pin_by_name(spawn, "SpawnTransform", unreal.EdGraphPinDirection.EGPD_INPUT)
    break_all(spawn_xform)
    log(f"Transform wire={connect(xform_out, spawn_xform)} out={xform_out} in={spawn_xform}")

    # Class sanity
    class_pin = pin_by_name(spawn, "Class", unreal.EdGraphPinDirection.EGPD_INPUT)
    if class_pin:
        log(f"Class={unreal.BlueprintGraphPinLibrary.get_pin_value(class_pin)!r}")

    coll = pin_by_name(spawn, "CollisionHandlingOverride", unreal.EdGraphPinDirection.EGPD_INPUT)
    if coll:
        try:
            coll.set_pin_value("AlwaysSpawn")
            log("AlwaysSpawn")
        except Exception as exc:
            log(f"AlwaysSpawn skipped: {exc}")

    bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(SPAWN_BP, only_if_is_dirty=False)
    log("Saved")

    for node in eg.list_all_nodes():
        log(f"FINAL {node.get_name()} | {node.get_class().get_name()} | {str(node.get_node_title()).replace(chr(10),' ')}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log(f"FATAL: {exc}")
        raise
