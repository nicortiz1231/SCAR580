"""Attach SCARSniperAdsCameraComponent to BP_FPCharacter."""
import unreal
from pathlib import Path

BP_ASSET = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter"
COMPONENT_CLASS = "/Script/SCAR.SCARSniperAdsCameraComponent"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/wire_sniper_ads_camera.log")


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[sniper_ads_cam] {msg}")


def blueprint_has_component(bp, name: str) -> bool:
    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    for handle in subsystem.k2_gather_subobject_data_for_blueprint(bp):
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(
            unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        )
        if obj and name in obj.get_name():
            return True
    return False


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    bp = unreal.load_asset(BP_ASSET)
    if not bp:
        raise RuntimeError(f"Missing {BP_ASSET}")

    component_class = unreal.load_class(None, COMPONENT_CLASS)
    if not component_class:
        raise RuntimeError("SCARSniperAdsCameraComponent not compiled — build SCAR module first")

    if blueprint_has_component(bp, "SCARSniperAdsCamera"):
        log("Component already present")
        return

    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = subsystem.k2_gather_subobject_data_for_blueprint(bp)
    if not handles:
        raise RuntimeError("No subobject handles")

    params = unreal.AddNewSubobjectParams()
    params.parent_handle = handles[0]
    params.new_class = component_class
    params.blueprint_context = bp

    result, fail_reason = subsystem.add_new_subobject(params)
    if fail_reason and str(fail_reason).strip():
        raise RuntimeError(f"Add component failed: {fail_reason}")

    subsystem.rename_subobject(result, "SCARSniperAdsCamera")
    bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter", only_if_is_dirty=False)
    log("Added SCARSniperAdsCameraComponent")


main()
