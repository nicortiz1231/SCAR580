"""Enumerate BP_FPCharacter subobjects via SubobjectDataSubsystem."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_subobjects_sds.log")
lines = []


def p(msg):
    lines.append(str(msg))
    unreal.log(msg)


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
handles = sds.k2_gather_subobject_data_for_blueprint(bp)
p(f"handles={len(handles)}")

for handle in handles:
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    name = unreal.SubobjectDataBlueprintFunctionLibrary.get_display_name(data)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
    cls = obj.get_class().get_name() if obj else "None"
    p(f"  {name} class={cls} obj={obj}")
    if obj and "CameraComponent" in cls:
        settings = obj.post_process_settings
        p(f"    apply_physical={settings.get_editor_property('auto_exposure_apply_physical_camera_exposure')}")
        p(f"    override_apply_physical={settings.get_editor_property('override_auto_exposure_apply_physical_camera_exposure')}")
        p(f"    method={settings.get_editor_property('auto_exposure_method')}")
        try:
            blendables = settings.get_editor_property("weighted_blendables")
            p(f"    blendables={blendables}")
        except Exception as exc:
            p(f"    blendables ERR {exc}")

LOG.write_text("\n".join(lines))
