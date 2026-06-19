import unreal
from pathlib import Path
LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_light_defaults.log")
lines = []
bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
for handle in sds.k2_gather_subobject_data_for_blueprint(bp):
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
    if not obj or "KeyLight" not in obj.get_name():
        continue
    for prop in ("intensity", "intensity_units", "attenuation_radius", "use_inverse_squared_falloff", "mobility"):
        try:
            lines.append(f"{obj.get_name()}.{prop}={obj.get_editor_property(prop)}")
        except Exception as exc:
            lines.append(f"{prop} ERR {exc}")
LOG.write_text("\n".join(lines))
