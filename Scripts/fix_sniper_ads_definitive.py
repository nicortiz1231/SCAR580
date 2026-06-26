"""Definitive sniper ADS: safe weapon distance + FOV zoom, no clip hacks."""
import unreal
from pathlib import Path
import re

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_sniper_ads_definitive.log")
CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
SNIPER_PATH = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper"
DT_PATH = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/DT_SniperAnimationValues"
ENGINE_INI = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Config/DefaultEngine.ini")

SELECT_NODE = "K2Node_Select_5"
SNIPER_FOV_ENUM = "NewEnumerator14"

# Original Bodycam aim distance — known safe, no mesh clip.
AIM_DISTANCE = 5.0
# Zoom ADS camera so scope fills screen without moving mesh closer.
SNIPER_ADS_FOV = 32.0
SCOPE_SIGHT_DISTANCE = 600.0
SCOPE_GRADIENT_PARAM = 600.0

# Bodycam original-ish pose — weapon not pushed into near plane.
TARGET_BASE_POSE_LOC = unreal.Vector(-10.93, 30.50, 10.25)
NEAR_CLIP = "1.0"

# Bypass broken optic hide nodes inserted after Aim().
BYPASS_SETVIS = ("K2Node_CallFunction_194", "K2Node_CallFunction_204")
# Remove redundant near-clip nodes inserted on AIMOn/AIMOff (console cmd unreliable on iOS).
REMOVE_NEARCLIP_NODES = ("K2Node_CallFunction_165", "K2Node_CallFunction_190", "K2Node_CallFunction_191")


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[sniper_ads_def] {msg}")


def find_node(editor, name: str):
    for node in editor.list_all_nodes():
        if node.get_name() == name:
            return node
    return None


def connect_exec(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def bypass_setvisibility_nodes(editor) -> None:
    for vis_name in BYPASS_SETVIS:
        vis = find_node(editor, vis_name)
        if not vis:
            log(f"No SetVisibility node {vis_name}")
            continue
        exec_in = vis.find_input_pin("execute")
        exec_out = vis.find_output_pin("then")
        if not exec_in or not exec_out:
            continue
        upstream = [
            lp
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(exec_in)
            if lp.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_OUTPUT
        ]
        downstream = [
            lp
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(exec_out)
            if lp.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT
        ]
        for up in upstream:
            up.break_pin_links()
            for down in downstream:
                connect_exec(up, down)
        editor.remove_nodes([vis])
        log(f"Removed bypass SetVisibility {vis_name}")


def remove_nearclip_nodes(editor) -> None:
    remove = []
    for name in REMOVE_NEARCLIP_NODES:
        node = find_node(editor, name)
        if node:
            remove.append(node)
    if not remove:
        log("No extra near-clip nodes to remove")
        return

    for node in remove:
        exec_in = node.find_input_pin("execute")
        exec_out = node.find_output_pin("then")
        if not exec_in or not exec_out:
            continue
        upstream = [
            lp
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(exec_in)
            if lp.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_OUTPUT
        ]
        downstream = [
            lp
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(exec_out)
            if lp.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT
        ]
        for up in upstream:
            up.break_pin_links()
            for down in downstream:
                connect_exec(up, down)

    editor.remove_nodes(remove)
    log(f"Removed {len(remove)} redundant near-clip console nodes")


def normalize_nearclip_cmds(editor) -> None:
    for node in editor.list_all_nodes():
        if "ExecuteConsoleCommand" not in str(node.get_node_title()):
            continue
        pin = node.find_input_pin("Command")
        if not pin:
            continue
        val = str(unreal.BlueprintGraphPinLibrary.get_pin_value(pin) or "")
        if "SetNearClipPlane" in val and NEAR_CLIP not in val:
            pin.set_pin_value(f"r.SetNearClipPlane {NEAR_CLIP}")
            log(f"Normalized near clip -> {NEAR_CLIP}")


def set_sniper_ads_fov(char_bp) -> None:
    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
    )
    select = find_node(editor, SELECT_NODE)
    if not select:
        raise RuntimeError(f"Missing {SELECT_NODE}")
    pin = select.find_input_pin(SNIPER_FOV_ENUM)
    if not pin:
        raise RuntimeError(f"Missing {SNIPER_FOV_ENUM}")
    old = unreal.BlueprintGraphPinLibrary.get_pin_value(pin) or "?"
    pin.set_pin_value(str(SNIPER_ADS_FOV))
    log(f"Sniper ADS FOV ({SNIPER_FOV_ENUM}): {old} -> {SNIPER_ADS_FOV}")


def tune_sniper(sniper_bp) -> None:
    cdo = unreal.get_default_object(sniper_bp.generated_class())
    for prop, val in (
        ("AimDistanceFromCamera", AIM_DISTANCE),
        ("ScopeMat_SightDistance", SCOPE_SIGHT_DISTANCE),
        ("ScopeMat_GradientParam", SCOPE_GRADIENT_PARAM),
    ):
        old = cdo.get_editor_property(prop)
        cdo.set_editor_property(prop, val)
        log(f"{prop}: {old} -> {val}")
    sniper_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(sniper_bp)
    unreal.EditorAssetLibrary.save_asset(SNIPER_PATH, only_if_is_dirty=False)


def tune_dt_pose(dt) -> None:
    wv = dt.get_editor_property("WeaponValues")
    loc = wv.get_editor_property("BasePoseLoc")
    old = (float(loc.x), float(loc.y), float(loc.z))
    wv.set_editor_property("BasePoseLoc", TARGET_BASE_POSE_LOC)
    dt.set_editor_property("WeaponValues", wv)
    dt.modify()
    unreal.EditorAssetLibrary.save_asset(DT_PATH, only_if_is_dirty=False)
    t = TARGET_BASE_POSE_LOC
    log(f"BasePoseLoc {old} -> ({t.x},{t.y},{t.z})")


def tune_engine_ini() -> None:
    text = ENGINE_INI.read_text()
    new_text, n = re.subn(r"(NearClipPlane=)[0-9.]+", rf"\g<1>{NEAR_CLIP}", text, count=1)
    if n:
        ENGINE_INI.write_text(new_text)
        log(f"DefaultEngine.ini NearClipPlane -> {NEAR_CLIP}")


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    char_bp = unreal.load_asset(f"{CHAR_BP}.BP_FPCharacter")
    sniper_bp = unreal.load_asset(f"{SNIPER_PATH}.BP_Weapon_Sniper")
    dt = unreal.load_asset(f"{DT_PATH}.DT_SniperAnimationValues")
    if not all((char_bp, sniper_bp, dt)):
        raise RuntimeError("Missing assets")

    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
    )
    bypass_setvisibility_nodes(editor)
    remove_nearclip_nodes(editor)
    normalize_nearclip_cmds(editor)
    set_sniper_ads_fov(char_bp)

    tune_sniper(sniper_bp)
    tune_dt_pose(dt)
    tune_engine_ini()

    char_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(char_bp)
    unreal.EditorAssetLibrary.save_asset(CHAR_BP, only_if_is_dirty=False)
    log("Done — safe aim distance + ADS FOV zoom; scope/sniper mesh should not clip")


main()
