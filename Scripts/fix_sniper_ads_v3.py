"""Sniper ADS v3: moderate aim pull + strong FOV zoom + scope shader defaults."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_sniper_ads_v3.log")
CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
SNIPER_PATH = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper"
DT_PATH = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/DT_SniperAnimationValues"

SELECT_NODE = "K2Node_Select_5"
SNIPER_FOV_ENUM = "NewEnumerator14"

# Closer eyepiece with C++ near-clip (0.05) handling mesh proximity.
AIM_DISTANCE = 4.25
SNIPER_ADS_FOV = 22.0
SCOPE_SIGHT_DISTANCE = 650.0
SCOPE_GRADIENT_PARAM = 620.0
SCOPE_RENDER_RADIUS = 1.35
# Original Bodycam base pose — proven non-clipping in kit.
TARGET_BASE_POSE_LOC = unreal.Vector(-10.93, 32.64, 11.01)


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[sniper_ads_v3] {msg}")


def find_node(editor, name: str):
    for node in editor.list_all_nodes():
        if node.get_name() == name:
            return node
    return None


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
    select = find_node(editor, SELECT_NODE)
    pin = select.find_input_pin(SNIPER_FOV_ENUM)
    old_fov = unreal.BlueprintGraphPinLibrary.get_pin_value(pin) or "?"
    pin.set_pin_value(str(SNIPER_ADS_FOV))
    log(f"ADS FOV: {old_fov} -> {SNIPER_ADS_FOV}")

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

    wv = dt.get_editor_property("WeaponValues")
    loc = wv.get_editor_property("BasePoseLoc")
    old = (loc.x, loc.y, loc.z)
    wv.set_editor_property("BasePoseLoc", TARGET_BASE_POSE_LOC)
    dt.set_editor_property("WeaponValues", wv)
    dt.modify()
    unreal.EditorAssetLibrary.save_asset(DT_PATH, only_if_is_dirty=False)
    t = TARGET_BASE_POSE_LOC
    log(f"BasePoseLoc {old} -> ({t.x},{t.y},{t.z})")

    sniper_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(sniper_bp)
    unreal.EditorAssetLibrary.save_asset(SNIPER_PATH, only_if_is_dirty=False)

    char_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(char_bp)
    unreal.EditorAssetLibrary.save_asset(CHAR_BP, only_if_is_dirty=False)
    log("Done")


main()
