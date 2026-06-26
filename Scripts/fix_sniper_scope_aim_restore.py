"""Restore Bodycam scope dual-render: AIMOn/AIMOff -> ScopeRef -> Aim()."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_sniper_scope_aim_restore.log")
CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
SNIPER_PATH = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper"
SELECT_NODE = "K2Node_Select_5"
SNIPER_FOV_ENUM = "NewEnumerator14"
SNIPER_ADS_CAMERA_FOV = 70.0
SCOPE_SIGHT_DISTANCE = 1200.0
SCOPE_GRADIENT_PARAM = 950.0
AIM_DISTANCE = 8.0

AIM_ON_FN = "K2Node_CallFunction_56"
AIM_OFF_FN = "K2Node_CallFunction_379"
MOBILE_ON_SET = "K2Node_VariableSet_27"
MOBILE_OFF_SET = "K2Node_VariableSet_49"
SCOPE_GET_ON = "K2Node_VariableGet_81"
SCOPE_GET_OFF = "K2Node_VariableGet_191"


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[scope_aim_restore] {msg}")


def connect_exec(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def find_node(editor, name: str):
    for node in editor.list_all_nodes():
        if node.get_name() == name:
            return node
    return None


def rewire_aim_on_off(editor) -> None:
    aim_on = find_node(editor, AIM_ON_FN)
    aim_off = find_node(editor, AIM_OFF_FN)
    get_on = find_node(editor, SCOPE_GET_ON)
    get_off = find_node(editor, SCOPE_GET_OFF)
    mob_on = find_node(editor, MOBILE_ON_SET)
    mob_off = find_node(editor, MOBILE_OFF_SET)
    if not all((aim_on, aim_off, get_on, get_off)):
        raise RuntimeError("Missing AIMOn/AIMOff or ScopeRef get nodes")

    # AIMOn -> MobileAdsTouchActive -> Get ScopeRef (exec)
    aim_on_then = aim_on.find_output_pin("then")
    if aim_on_then:
        aim_on_then.break_pin_links()

    if mob_on:
        connect_exec(aim_on_then, mob_on.find_input_pin("execute"))
        mob_then = mob_on.find_output_pin("then")
        if mob_then:
            mob_then.break_pin_links()
            connect_exec(mob_then, get_on.find_input_pin("execute"))
            log("Wired AIMOn -> MobileAdsTouchActive -> ScopeRef Get (on)")
        else:
            connect_exec(aim_on_then, get_on.find_input_pin("execute"))
            log("Wired AIMOn -> ScopeRef Get (on), no mobile set then pin")
    else:
        connect_exec(aim_on_then, get_on.find_input_pin("execute"))
        log("Wired AIMOn -> ScopeRef Get (on)")

    # AIMOff -> MobileAdsTouchActive -> Get ScopeRef (off)
    aim_off_then = aim_off.find_output_pin("then")
    if aim_off_then:
        aim_off_then.break_pin_links()

    if mob_off:
        connect_exec(aim_off_then, mob_off.find_input_pin("execute"))
        mob_off_then = mob_off.find_output_pin("then")
        if mob_off_then:
            mob_off_then.break_pin_links()
            connect_exec(mob_off_then, get_off.find_input_pin("execute"))
            log("Wired AIMOff -> MobileAdsTouchActive -> ScopeRef Get (off)")
        else:
            connect_exec(aim_off_then, get_off.find_input_pin("execute"))
    else:
        connect_exec(aim_off_then, get_off.find_input_pin("execute"))
        log("Wired AIMOff -> ScopeRef Get (off)")


def restore_camera_fov(char_bp) -> None:
    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
    )
    select = find_node(editor, SELECT_NODE)
    if not select:
        raise RuntimeError(f"Missing {SELECT_NODE}")
    pin = select.find_input_pin(SNIPER_FOV_ENUM)
    pin.set_pin_value(str(SNIPER_ADS_CAMERA_FOV))
    log(f"Camera ADS FOV -> {SNIPER_ADS_CAMERA_FOV}")


def tune_sniper_scope(sniper_bp) -> None:
    cdo = unreal.get_default_object(sniper_bp.generated_class())
    for prop, val in (
        ("ScopeMat_SightDistance", SCOPE_SIGHT_DISTANCE),
        ("ScopeMat_GradientParam", SCOPE_GRADIENT_PARAM),
        ("AimDistanceFromCamera", AIM_DISTANCE),
    ):
        cdo.set_editor_property(prop, val)
        log(f"{prop} -> {val}")
    sniper_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(sniper_bp)
    unreal.EditorAssetLibrary.save_asset(SNIPER_PATH, only_if_is_dirty=False)


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
    rewire_aim_on_off(editor)
    restore_camera_fov(char_bp)

    char_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(char_bp)
    unreal.EditorAssetLibrary.save_asset(CHAR_BP, only_if_is_dirty=False)

    tune_sniper_scope(sniper_bp)
    log("Done")


main()
