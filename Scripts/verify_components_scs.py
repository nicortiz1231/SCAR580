import unreal
from pathlib import Path

LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/verify_components_scs.log")
if LOG_PATH.exists():
    LOG_PATH.unlink()


def log(msg: str) -> None:
    with LOG_PATH.open("a") as f:
        f.write(msg + "\n")
    unreal.log(msg)


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
handles = subsystem.k2_gather_subobject_data_for_blueprint(bp)
log(f"Total subobject handles: {len(handles)}")
for handle in handles:
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
    if obj:
        log(f"  {obj.get_name()} | {obj.get_class().get_name()}")

log("=== CDO components ===")
cdo = unreal.get_default_object(bp.generated_class())
for comp in cdo.get_components_by_class(unreal.ActorComponent.static_class()):
    log(f"  CDO comp: {comp.get_name()} | {comp.get_class().get_name()}")

log("done")
