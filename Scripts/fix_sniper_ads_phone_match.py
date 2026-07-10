"""Restore sniper ADS to editor close-up: main FOV 18 (works on mobile; FP rendering does not)."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_sniper_ads_phone_match.log")
CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
SNIPER_PATH = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper"

SELECT_NODE = "K2Node_Select_5"
SNIPER_FOV_ENUM = "NewEnumerator14"
SNIPER_ADS_FOV = 18.0
AIM_DISTANCE = 15.0


def log(msg: str) -> None:
    prev = LOG.read_text() if LOG.exists() else ""
    LOG.write_text(prev + msg + "\n")
    unreal.log(f"[sniper_ads_phone] {msg}")


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
    if not char_bp or not sniper_bp:
        raise RuntimeError("Missing character or sniper blueprint")

    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
    )
    select = find_node(editor, SELECT_NODE)
    if not select:
        raise RuntimeError(f"Missing {SELECT_NODE}")

    pin = select.find_input_pin(SNIPER_FOV_ENUM)
    if not pin:
        raise RuntimeError(f"Missing pin {SNIPER_FOV_ENUM}")

    old = unreal.BlueprintGraphPinLibrary.get_pin_value(pin) or "?"
    pin.set_pin_value(str(SNIPER_ADS_FOV))
    log(f"Sniper ADS FOV ({SNIPER_FOV_ENUM}): {old} -> {SNIPER_ADS_FOV}")

    # Keep FirstPersonCamera FP path enabled for editor parity (ignored on mobile, harmless).
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
        obj.set_editor_property("first_person_scale", 2.5)
        log("FirstPersonCamera: FP FOV/scale re-enabled for editor")
        break

    cdo = unreal.get_default_object(sniper_bp.generated_class())
    old_aim = cdo.get_editor_property("AimDistanceFromCamera")
    cdo.set_editor_property("AimDistanceFromCamera", AIM_DISTANCE)
    log(f"AimDistanceFromCamera: {old_aim} -> {AIM_DISTANCE}")

    for bp, path in ((char_bp, CHAR_BP), (sniper_bp, SNIPER_PATH)):
        bp.modify()
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)

    # Verify
    verify = unreal.BlueprintGraphPinLibrary.get_pin_value(
        find_node(
            unreal.BlueprintGraphEditor.get_graph_editor(
                unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
            ),
            SELECT_NODE,
        ).find_input_pin(SNIPER_FOV_ENUM)
    )
    log(f"Verified NewEnumerator14={verify}")
    log("Done")


main()
