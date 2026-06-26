"""Reference-style sniper ADS: shader ring at safe distance + early near clip."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_sniper_scope_reference.log")
CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
SNIPER_PATH = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper"
ENGINE_INI = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Config/DefaultEngine.ini")

AIM_ON_FN = "K2Node_CallFunction_56"
AIM_OFF_FN = "K2Node_CallFunction_379"
MOBILE_ON_SET = "K2Node_VariableSet_27"
AIM_ON_EVENT = "K2Node_CustomEvent_16"
AIM_OFF_EVENT = "K2Node_CustomEvent_19"
EXEC_CMD_FN = "/Script/Engine.KismetSystemLibrary:ExecuteConsoleCommand"

# Slightly closer than original 5.0 but safe with near clip 0.1 + scope shader ring.
AIM_DISTANCE = 4.0
SCOPE_SIGHT_DISTANCE = 600.0
SCOPE_GRADIENT_PARAM = 600.0
SCOPE_RENDER_RADIUS = 1.25
ADS_NEAR_CLIP = "0.1"
HIP_NEAR_CLIP = "1.0"
ENGINE_NEAR_CLIP = "1.000000"


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[scope_reference] {msg}")


def find_node(editor, name: str):
    for node in editor.list_all_nodes():
        if node.get_name() == name:
            return node
    return None


def connect_exec(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def make_exec_cmd(editor, command: str):
    node = editor.add_call_function_node(EXEC_CMD_FN)
    if not node:
        raise RuntimeError("Failed to spawn ExecuteConsoleCommand")
    pin = node.find_input_pin("WorldContextObject")
    if pin:
        pin.set_pin_value("self")
    cmd = node.find_input_pin("Command")
    if cmd:
        cmd.set_pin_value(command)
    return node


def insert_exec_cmd_first(editor, source_node_name: str, command: str, label: str) -> None:
    """Run near-clip change before any other AIMOn/AIMOff work."""
    source = find_node(editor, source_node_name)
    if not source:
        log(f"WARN: missing {source_node_name} for {label}")
        return

    then = source.find_output_pin("then")
    if not then:
        log(f"WARN: {source_node_name} has no then pin")
        return

    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
        owner = lp.get_owning_node()
        if "ExecuteConsoleCommand" in str(owner.get_node_title()):
            cmd_pin = owner.find_input_pin("Command")
            if cmd_pin and command in str(unreal.BlueprintGraphPinLibrary.get_pin_value(cmd_pin) or ""):
                log(f"{label} near clip already first: {command}")
                return

    downstream = list(unreal.BlueprintGraphPinLibrary.list_connected_pins(then))
    cmd_node = make_exec_cmd(editor, command)
    cmd_exec = cmd_node.find_input_pin("execute")
    cmd_then = cmd_node.find_output_pin("then")
    then.break_pin_links()
    connect_exec(then, cmd_exec)
    for pin in downstream:
        connect_exec(cmd_then, pin)
    log(f"Inserted {label} -> ExecuteConsoleCommand({command!r}) before downstream")


def update_all_near_clip_cmds(editor) -> None:
    ads_values = {"0.8", "4.5", "5.0", "5", "0.5"}
    hip_values = {"1.0", "1", "2.5", "3.25", "3.250000"}
    for node in editor.list_all_nodes():
        if "ExecuteConsoleCommand" not in str(node.get_node_title()):
            continue
        pin = node.find_input_pin("Command")
        if not pin:
            continue
        val = str(unreal.BlueprintGraphPinLibrary.get_pin_value(pin) or "")
        if "SetNearClipPlane" not in val:
            continue
        try:
            current = val.split()[-1]
        except IndexError:
            continue
        if current in ads_values or float(current) > 1.05:
            pin.set_pin_value(f"r.SetNearClipPlane {ADS_NEAR_CLIP}")
            log(f"ADS near clip cmd {current} -> {ADS_NEAR_CLIP}")
        elif current in hip_values:
            pin.set_pin_value(f"r.SetNearClipPlane {HIP_NEAR_CLIP}")
            log(f"Hip near clip cmd {current} -> {HIP_NEAR_CLIP}")


def tune_sniper(sniper_bp) -> None:
    cdo = unreal.get_default_object(sniper_bp.generated_class())
    for prop, val in (
        ("AimDistanceFromCamera", AIM_DISTANCE),
        ("ScopeMat_SightDistance", SCOPE_SIGHT_DISTANCE),
        ("ScopeMat_GradientParam", SCOPE_GRADIENT_PARAM),
        ("ScopeRenderRadius", SCOPE_RENDER_RADIUS),
    ):
        old = cdo.get_editor_property(prop)
        cdo.set_editor_property(prop, val)
        log(f"{prop}: {old} -> {val}")
    sniper_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(sniper_bp)
    unreal.EditorAssetLibrary.save_asset(SNIPER_PATH, only_if_is_dirty=False)


def update_engine_ini() -> None:
    import re

    text = ENGINE_INI.read_text()
    new_text, n = re.subn(
        r"(NearClipPlane=)[0-9.]+",
        rf"\g<1>{ENGINE_NEAR_CLIP}",
        text,
        count=1,
    )
    if n:
        ENGINE_INI.write_text(new_text)
        log(f"DefaultEngine.ini NearClipPlane -> {ENGINE_NEAR_CLIP}")


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    char_bp = unreal.load_asset(f"{CHAR_BP}.BP_FPCharacter")
    sniper_bp = unreal.load_asset(f"{SNIPER_PATH}.BP_Weapon_Sniper")
    if not char_bp or not sniper_bp:
        raise RuntimeError("Missing blueprints")

    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
    )

    # Near clip before weapon lerp and before scope Aim().
    insert_exec_cmd_first(editor, AIM_ON_FN, f"r.SetNearClipPlane {ADS_NEAR_CLIP}", "AIMOn")
    insert_exec_cmd_first(editor, AIM_ON_EVENT, f"r.SetNearClipPlane {ADS_NEAR_CLIP}", "AIMOnEvent")
    insert_exec_cmd_first(editor, AIM_OFF_FN, f"r.SetNearClipPlane {HIP_NEAR_CLIP}", "AIMOff")
    insert_exec_cmd_first(editor, AIM_OFF_EVENT, f"r.SetNearClipPlane {HIP_NEAR_CLIP}", "AIMOffEvent")
    update_all_near_clip_cmds(editor)

    tune_sniper(sniper_bp)
    update_engine_ini()

    char_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(char_bp)
    unreal.EditorAssetLibrary.save_asset(CHAR_BP, only_if_is_dirty=False)
    log("Done — Bodycam reference ADS: shader ring at safe distance, near clip 0.1 before ADS")


main()
