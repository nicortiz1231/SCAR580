"""Dump 5.7-equivalent lighting: lights, camera PP, PPV."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_57_lighting.log")
lines = []


def dump_pp(settings, label):
    keys = (
        "auto_exposure_method",
        "auto_exposure_bias",
        "auto_exposure_min_brightness",
        "auto_exposure_max_brightness",
        "auto_exposure_apply_physical_camera_exposure",
        "override_auto_exposure_apply_physical_camera_exposure",
        "bloom_intensity",
        "override_bloom_intensity",
    )
    for key in keys:
        try:
            lines.append(f"{label}.{key}={settings.get_editor_property(key)}")
        except Exception:
            pass


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
seen = set()
for handle in sds.k2_gather_subobject_data_for_blueprint(bp):
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
    if not obj:
        continue
    oid = id(obj)
    if oid in seen:
        continue
    seen.add(oid)
    cn = obj.get_class().get_name()
    if "Light" in cn:
        lines.append(
            f"LIGHT {obj.get_name()} intensity={obj.get_editor_property('intensity')} "
            f"radius={obj.get_editor_property('attenuation_radius')} "
            f"falloff={obj.get_editor_property('use_inverse_squared_falloff')}"
        )
    if "FirstPersonCamera" in obj.get_name():
        dump_pp(obj.post_process_settings, "CAMERA")

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
if world:
    for vol in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PostProcessVolume.static_class()):
        lines.append(f"PPV unbound={vol.get_editor_property('unbound')}")
        dump_pp(vol.settings, "PPV")

LOG.write_text("\n".join(lines))
