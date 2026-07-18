import unreal
from pathlib import Path

LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/finish_presentation_config2.log")
if LOG_PATH.exists():
    LOG_PATH.unlink()

BP_FP_CHARACTER = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
OPPONENT_MIRROR_ANIM = "/Game/BodycamFPSKIT/Demo/Character/Mannequins/Animations/ABP_Mirror.ABP_Mirror_C"
OPPONENT_POSE_DRIVER_ANIM = "/Game/BodycamFPSKIT/Character/ABP_FP_ArmsProcedural.ABP_FP_ArmsProcedural_C"


def log(msg: str) -> None:
    with LOG_PATH.open("a") as f:
        f.write(str(msg) + "\n")
    unreal.log(str(msg))


def set_prop(obj, names, value) -> bool:
    for name in names:
        try:
            obj.set_editor_property(name, value)
            log(f"Set {obj.get_name()}.{name} = {value}")
            return True
        except Exception as exc:
            log(f"Skip {name}: {exc}")
    return False


bp = unreal.load_asset(f"{BP_FP_CHARACTER}.BP_FPCharacter")
subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
handles = subsystem.k2_gather_subobject_data_for_blueprint(bp)

presentation = None
for handle in handles:
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
    if obj and "SCARMultiplayerPresentationComponent" in obj.get_class().get_name():
        presentation = obj
        break

if not presentation:
    log("ERROR: could not find SCARMultiplayerPresentation component template")
else:
    log(f"Found presentation component template: {presentation.get_name()}")

    mirror_anim = unreal.load_class(None, OPPONENT_MIRROR_ANIM)
    pose_anim = unreal.load_class(None, OPPONENT_POSE_DRIVER_ANIM)
    log(f"mirror_anim resolved: {mirror_anim}")
    log(f"pose_anim resolved: {pose_anim}")

    set_prop(presentation, ("opponent_mirror_anim_class", "OpponentMirrorAnimClass"), mirror_anim)
    set_prop(presentation, ("opponent_pose_driver_anim_class", "OpponentPoseDriverAnimClass"), pose_anim)
    set_prop(presentation, ("opponent_weapon_attach_socket_name", "OpponentWeaponAttachSocketName"), "ik_hand_gun")
    set_prop(
        presentation,
        ("pose_driver_relative_location", "PoseDriverRelativeLocation"),
        unreal.Vector(15.0, 0.0, 65.0),
    )
    set_prop(presentation, ("b_show_opponent_debug", "bShowOpponentDebug"), False)

    # Read back to confirm values actually stuck.
    for prop in ("OpponentMirrorAnimClass", "OpponentPoseDriverAnimClass", "OpponentWeaponAttachSocketName"):
        try:
            log(f"Readback {prop} = {presentation.get_editor_property(prop)}")
        except Exception as exc:
            log(f"Readback {prop} failed: {exc}")

unreal.BlueprintEditorLibrary.compile_blueprint(bp)
unreal.EditorAssetLibrary.save_asset(BP_FP_CHARACTER, only_if_is_dirty=False)
log("Compiled + saved BP_FPCharacter")
log("done")
