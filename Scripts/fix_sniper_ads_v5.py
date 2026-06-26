"""Sniper ADS v5: safe weapon distance + FP scale zoom — no mesh-in-camera clipping."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_sniper_ads_v5.log")
CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
SNIPER_PATH = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper"
SCOPE_BP = "/Game/BodycamFPSKIT/Blueprints/Attachments/Scope/Blueprints/BP_Scope"

SELECT_NODE = "K2Node_Select_5"
SNIPER_FOV_ENUM = "NewEnumerator14"
# Original Bodycam safe distance — weapon stays out of near-clip zone.
AIM_DISTANCE = 15.0
SNIPER_ADS_FOV = 18.0
FP_SCALE = 2.5


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[sniper_ads_v5] {msg}")


def find_node(editor, name: str):
    for node in editor.list_all_nodes():
        if node.get_name() == name:
            return node
    return None


def configure_first_person_camera(char_bp) -> None:
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    for handle in sds.k2_gather_subobject_data_for_blueprint(char_bp):
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(
            unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        )
        if not obj or "FirstPersonCamera" not in obj.get_name():
            continue
        obj.set_editor_property("enable_first_person_field_of_view", True)
        obj.set_editor_property("enable_first_person_scale", True)
        obj.set_editor_property("first_person_field_of_view", SNIPER_ADS_FOV)
        obj.set_editor_property("first_person_scale", FP_SCALE)
        log(f"FirstPersonCamera FOV={SNIPER_ADS_FOV} scale={FP_SCALE}")
        return


def configure_scope_shader(scope_bp) -> None:
    cdo = unreal.get_default_object(scope_bp.generated_class())
    for prop, val in (
        ("ScopeMat_SightDistance", 600.0),
        ("ScopeMat_GradientParam", 600.0),
        ("ScopeRenderRadius", 1.25),
    ):
        try:
            old = cdo.get_editor_property(prop)
            cdo.set_editor_property(prop, val)
            log(f"{prop}: {old} -> {val}")
        except Exception as exc:
            log(f"Skip {prop}: {exc}")


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    char_bp = unreal.load_asset(f"{CHAR_BP}.BP_FPCharacter")
    sniper_bp = unreal.load_asset(f"{SNIPER_PATH}.BP_Weapon_Sniper")
    scope_bp = unreal.load_asset(f"{SCOPE_BP}.BP_Scope")
    if not char_bp or not sniper_bp:
        raise RuntimeError("Missing character or sniper blueprint")

    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
    )
    pin = find_node(editor, SELECT_NODE).find_input_pin(SNIPER_FOV_ENUM)
    old = unreal.BlueprintGraphPinLibrary.get_pin_value(pin) or "?"
    pin.set_pin_value(str(SNIPER_ADS_FOV))
    log(f"ADS FOV: {old} -> {SNIPER_ADS_FOV}")

    cdo = unreal.get_default_object(sniper_bp.generated_class())
    old_aim = cdo.get_editor_property("AimDistanceFromCamera")
    cdo.set_editor_property("AimDistanceFromCamera", AIM_DISTANCE)
    log(f"AimDistanceFromCamera: {old_aim} -> {AIM_DISTANCE}")

    configure_first_person_camera(char_bp)
    if scope_bp:
        configure_scope_shader(scope_bp)

    assets = [(char_bp, CHAR_BP), (sniper_bp, SNIPER_PATH)]
    if scope_bp:
        assets.append((scope_bp, SCOPE_BP))
    for bp, path in assets:
        bp.modify()
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
    log("Done — safe distance + FP scale zoom, no close-mesh pull")


main()
