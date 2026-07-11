"""Add SCARArLaserPresentationComponent to BP_FPCharacter."""
import unreal
from pathlib import Path

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
COMPONENT_CLASS = "/Script/SCAR.SCARArLaserPresentationComponent"
LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/wire_ar_laser_component.log")


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[wire_ar_laser_component] {msg}")


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
    if LOG.exists():
        LOG.unlink()

    bp = unreal.load_asset(BP_ASSET)
    if not bp:
        raise RuntimeError("Missing BP_FPCharacter")

    if blueprint_has_component(bp, "SCARArLaserPresentation"):
        log("Already has SCARArLaserPresentationComponent")
        return

    comp_class = unreal.load_class(None, COMPONENT_CLASS)
    if not comp_class:
        raise RuntimeError("SCARArLaserPresentationComponent not compiled")

    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = subsystem.k2_gather_subobject_data_for_blueprint(bp)
    if not handles:
        raise RuntimeError("No subobject handles on BP_FPCharacter")

    params = unreal.AddNewSubobjectParams()
    params.parent_handle = handles[0]
    params.new_class = comp_class
    params.blueprint_context = bp

    result, fail_reason = subsystem.add_new_subobject(params)
    if fail_reason and str(fail_reason).strip():
        raise RuntimeError(f"Failed to add component: {fail_reason}")

    subsystem.rename_subobject(result, "SCARArLaserPresentation")
    bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)
    log("Added SCARArLaserPresentationComponent to BP_FPCharacter")


main()
