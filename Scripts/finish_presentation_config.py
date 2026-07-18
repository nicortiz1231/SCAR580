"""Finish configuring SCARMultiplayerPresentation now that the component actually exists post-compile."""

import unreal
from pathlib import Path

LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/finish_presentation_config.log")

BP_FP_CHARACTER = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"

OPPONENT_MIRROR_ANIM = (
    "/Game/BodycamFPSKIT/Demo/Character/Mannequins/Animations/ABP_Mirror.ABP_Mirror_C"
)
OPPONENT_POSE_DRIVER_ANIM = "/Game/BodycamFPSKIT/Character/ABP_FP_ArmsProcedural.ABP_FP_ArmsProcedural_C"


def log(msg: str) -> None:
    with LOG_PATH.open("a") as f:
        f.write(msg + "\n")
    unreal.log(f"[finish_presentation_config] {msg}")


def set_prop(obj, names, value) -> bool:
    for name in names:
        try:
            obj.set_editor_property(name, value)
            log(f"Set {obj.get_name()}.{name} = {value}")
            return True
        except Exception as exc:
            log(f"Skip {name}: {exc}")
    return False


def find_component_on_cdo(cdo, component_name: str):
    for component in cdo.get_components_by_class(unreal.ActorComponent.static_class()):
        name = component.get_name()
        class_name = component.get_class().get_name()
        if name.startswith(component_name) or component_name in class_name:
            return component
    return None


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    bp = unreal.load_asset(f"{BP_FP_CHARACTER}.BP_FPCharacter")
    if not bp:
        raise RuntimeError("Missing BP_FPCharacter")

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    log("Compiled BP_FPCharacter")

    cdo = unreal.get_default_object(bp.generated_class())

    for comp_name in ("SCARARPoseSync", "SCARMultiplayerPresentation", "SCARMultiplayerHealth", "SCARMultiplayerCombat"):
        comp = find_component_on_cdo(cdo, comp_name)
        log(f"{comp_name} present on CDO: {comp is not None}")

    presentation = find_component_on_cdo(cdo, "SCARMultiplayerPresentation")
    if not presentation:
        log("ERROR: SCARMultiplayerPresentation still not found after compile")
        unreal.EditorAssetLibrary.save_asset(BP_FP_CHARACTER, only_if_is_dirty=False)
        return

    mirror_anim = unreal.load_class(None, OPPONENT_MIRROR_ANIM)
    pose_anim = unreal.load_class(None, OPPONENT_POSE_DRIVER_ANIM)
    log(f"mirror_anim resolved: {mirror_anim}")
    log(f"pose_anim resolved: {pose_anim}")

    set_prop(presentation, ("opponent_mirror_anim_class", "OpponentMirrorAnimClass"), mirror_anim)
    set_prop(presentation, ("opponent_pose_driver_anim_class", "OpponentPoseDriverAnimClass"), pose_anim)
    set_prop(
        presentation,
        ("opponent_weapon_attach_socket_name", "OpponentWeaponAttachSocketName"),
        "ik_hand_gun",
    )
    set_prop(
        presentation,
        ("pose_driver_relative_location", "PoseDriverRelativeLocation"),
        unreal.Vector(15.0, 0.0, 65.0),
    )
    set_prop(presentation, ("b_show_opponent_debug", "bShowOpponentDebug"), False)

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_FP_CHARACTER, only_if_is_dirty=False)
    log("Saved BP_FPCharacter")


main()
