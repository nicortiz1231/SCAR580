"""Sniper ADS v4: close aim + strong FOV (near clip handled in C++ camera modifier)."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_sniper_ads_v4.log")
CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
SNIPER_PATH = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper"

SELECT_NODE = "K2Node_Select_5"
SNIPER_FOV_ENUM = "NewEnumerator14"
AIM_DISTANCE = 3.75
SNIPER_ADS_FOV = 24.0


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[sniper_ads_v4] {msg}")


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
        obj.set_editor_property("first_person_scale", 1.0)
        log("Enabled FirstPersonCamera FP FOV/scale")
        return


def tag_sniper_meshes_first_person(sniper_bp) -> None:
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    count = 0
    for handle in sds.k2_gather_subobject_data_for_blueprint(sniper_bp):
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(
            unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        )
        if not obj or obj.get_class().get_name() not in ("StaticMeshComponent", "SkeletalMeshComponent"):
            continue
        name = obj.get_name()
        if not any(k in name for k in ("Optic", "Weapon", "Scope", "Mesh", "Skeletal")):
            continue
        try:
            obj.set_editor_property("first_person_primitive_type", unreal.FirstPersonPrimitiveType.FIRST_PERSON)
            count += 1
        except Exception:
            pass
    log(f"Tagged {count} sniper template meshes as FirstPerson")


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    char_bp = unreal.load_asset(f"{CHAR_BP}.BP_FPCharacter")
    sniper_bp = unreal.load_asset(f"{SNIPER_PATH}.BP_Weapon_Sniper")
    if not char_bp or not sniper_bp:
        raise RuntimeError("Missing assets")

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
    tag_sniper_meshes_first_person(sniper_bp)

    for bp, path in ((char_bp, CHAR_BP), (sniper_bp, SNIPER_PATH)):
        bp.modify()
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
    log("Done")


main()
