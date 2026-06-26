"""Tarkov-style sniper ADS: dual-render scope zoom + large eyepiece, no hip-fire change."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_sniper_scope_tarkov.log")
CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
SNIPER_PATH = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper"
SELECT_NODE = "K2Node_Select_5"
SNIPER_FOV_ENUM = "NewEnumerator14"

# Bodycam dual-FOV: main camera stays ~70°; scope shader magnifies the interior.
SNIPER_ADS_CAMERA_FOV = 70.0

# Scope material params (Aim On/Off feeds these into the scope shader).
SCOPE_SIGHT_DISTANCE = 1250.0
SCOPE_GRADIENT_PARAM = 920.0

# Closer than 11.5 so the eyepiece fills the view; still above pristine 5.0 for clip safety.
AIM_DISTANCE = 8.0


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[sniper_tarkov] {msg}")


def find_node(editor, name: str):
    for node in editor.list_all_nodes():
        if node.get_name() == name:
            return node
    return None


def restore_scope_camera_fov(char_bp) -> None:
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
    pin.set_pin_value(str(SNIPER_ADS_CAMERA_FOV))
    log(f"Camera ADS FOV ({SNIPER_FOV_ENUM}): {old} -> {SNIPER_ADS_CAMERA_FOV}")


def tune_sniper_scope_params(sniper_bp) -> None:
    cdo = unreal.get_default_object(sniper_bp.generated_class())
    for prop, val in (
        ("ScopeMat_SightDistance", SCOPE_SIGHT_DISTANCE),
        ("ScopeMat_GradientParam", SCOPE_GRADIENT_PARAM),
        ("AimDistanceFromCamera", AIM_DISTANCE),
    ):
        old = cdo.get_editor_property(prop)
        cdo.set_editor_property(prop, val)
        log(f"{prop}: {old} -> {val}")

    sniper_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(sniper_bp)
    unreal.EditorAssetLibrary.save_asset(SNIPER_PATH, only_if_is_dirty=False)


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    char_bp = unreal.load_asset(f"{CHAR_BP}.BP_FPCharacter")
    sniper_bp = unreal.load_asset(f"{SNIPER_PATH}.BP_Weapon_Sniper")
    if not char_bp or not sniper_bp:
        raise RuntimeError("Missing character or sniper blueprint")

    restore_scope_camera_fov(char_bp)
    char_bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(char_bp)
    unreal.EditorAssetLibrary.save_asset(CHAR_BP, only_if_is_dirty=False)

    tune_sniper_scope_params(sniper_bp)
    log("Done — dual-render scope zoom; hip-fire pose unchanged")


main()
