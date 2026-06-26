"""Eliminate brief ADS transition clip: pose nudge + near clip during aim."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_sniper_ads_transition.log")
CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
DT_PATH = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/DT_SniperAnimationValues"
SNIPER_PATH = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper"
AIM_ON_EVENT = "K2Node_CustomEvent_16"
AIM_OFF_EVENT = "K2Node_CustomEvent_19"
EXEC_CMD_FN = "/Script/Engine.KismetSystemLibrary:ExecuteConsoleCommand"
HIP_NEAR_CLIP = "2.5"
ADS_NEAR_CLIP = "4.5"
TARGET_BASE_POSE_LOC = unreal.Vector(-10.93, 24.00, 8.50)
AIM_DISTANCE = 11.5


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[sniper_ads_trans] {msg}")


def pin_value(pin, value: str) -> None:
    if pin:
        pin.set_pin_value(value)


def connect_exec(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def connect_data(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def find_node(editor, name: str):
    for node in editor.list_all_nodes():
        if node.get_name() == name:
            return node
    return None


def output_pin(node, preferred=None):
    if preferred:
        p = node.find_output_pin(preferred)
        if p:
            return p
    for p in unreal.BlueprintEditorLibrary.list_all_pins(node):
        if unreal.BlueprintGraphPinLibrary.get_pin_direction(p) == unreal.EdGraphPinDirection.EGPD_OUTPUT:
            return p
    return None


def has_exec_cmd_near_clip(editor, cmd: str) -> bool:
    for node in editor.list_all_nodes():
        if "ExecuteConsoleCommand" not in str(node.get_node_title()):
            continue
        pin = node.find_input_pin("Command")
        if pin and cmd in str(unreal.BlueprintGraphPinLibrary.get_pin_value(pin) or ""):
            return True
    return False


def make_exec_cmd_node(editor, command: str):
    node = editor.add_call_function_node(EXEC_CMD_FN)
    if not node:
        raise RuntimeError("Failed to spawn ExecuteConsoleCommand")
    pin_value(node.find_input_pin("WorldContextObject"), "self")
    cmd_pin = node.find_input_pin("Command")
    if cmd_pin:
        cmd_pin.set_pin_value(command)
    return node


def insert_exec_cmd_after_event(editor, event_name: str, command: str) -> None:
    if has_exec_cmd_near_clip(editor, command):
        log(f"{event_name} console cmd already present: {command}")
        return

    event = find_node(editor, event_name)
    if not event:
        raise RuntimeError(f"Missing {event_name}")

    then = event.find_output_pin("then")
    downstream = [
        lp
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then)
        if lp.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT
    ]

    # Skip if first downstream is already our near-clip cmd with same value.
    if downstream:
        owner = downstream[0].get_owning_node()
        if "ExecuteConsoleCommand" in str(owner.get_node_title()):
            pin = owner.find_input_pin("Command")
            if pin and command in str(unreal.BlueprintGraphPinLibrary.get_pin_value(pin) or ""):
                log(f"{event_name} already wired to {command}")
                return

    cmd_node = make_exec_cmd_node(editor, command)
    then.break_pin_links()
    connect_exec(then, cmd_node.find_input_pin("execute"))
    for pin in downstream:
        connect_exec(cmd_node.find_output_pin("then"), pin)
    log(f"Wired {event_name} -> ExecuteConsoleCommand({command!r})")


def tweak_dt_pose(dt) -> None:
    wv = dt.get_editor_property("WeaponValues")
    loc = wv.get_editor_property("BasePoseLoc")
    x, y, z = float(loc.x), float(loc.y), float(loc.z)
    wv.set_editor_property("BasePoseLoc", TARGET_BASE_POSE_LOC)
    dt.set_editor_property("WeaponValues", wv)
    dt.modify()
    unreal.EditorAssetLibrary.save_asset(DT_PATH, only_if_is_dirty=False)
    t = TARGET_BASE_POSE_LOC
    log(f"BasePoseLoc ({x:.2f},{y:.2f},{z:.2f}) -> ({t.x:.2f},{t.y:.2f},{t.z:.2f})")


def tweak_aim_distance(sniper_bp) -> None:
    cdo = unreal.get_default_object(sniper_bp.generated_class())
    current = float(cdo.get_editor_property("AimDistanceFromCamera"))
    cdo.set_editor_property("AimDistanceFromCamera", AIM_DISTANCE)
    sniper_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(sniper_bp)
    unreal.EditorAssetLibrary.save_asset(SNIPER_PATH, only_if_is_dirty=False)
    log(f"AimDistanceFromCamera {current} -> {AIM_DISTANCE}")


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    dt = unreal.load_asset(f"{DT_PATH}.DT_SniperAnimationValues")
    sniper = unreal.load_asset(f"{SNIPER_PATH}.BP_Weapon_Sniper")
    char_bp = unreal.load_asset(f"{CHAR_BP}.BP_FPCharacter")
    if not all((dt, sniper, char_bp)):
        raise RuntimeError("Missing assets")

    tweak_dt_pose(dt)
    tweak_aim_distance(sniper)

    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
    )
    insert_exec_cmd_after_event(editor, AIM_ON_EVENT, f"r.SetNearClipPlane {ADS_NEAR_CLIP}")
    insert_exec_cmd_after_event(editor, AIM_OFF_EVENT, f"r.SetNearClipPlane {HIP_NEAR_CLIP}")

    char_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(char_bp)
    unreal.EditorAssetLibrary.save_asset(CHAR_BP, only_if_is_dirty=False)
    log("Done")


main()
