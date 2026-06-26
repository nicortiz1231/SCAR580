import unreal
from pathlib import Path
OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_camera_clip_ue58.log")
lines = []
cam = unreal.CameraComponent.static_class()
cdo = unreal.get_default_object(cam)
for prop in sorted(dir(cdo)):
    if prop.startswith("_"):
        continue
    if "clip" in prop.lower() or "near" in prop.lower():
        try:
            lines.append(f"CameraComponent.{prop}={cdo.get_editor_property(prop)!r}")
        except Exception as exc:
            lines.append(f"CameraComponent.{prop} ERR {exc}")

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
for handle in sds.k2_gather_subobject_data_for_blueprint(bp):
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(
        unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    )
    if not obj or "FirstPersonCamera" not in obj.get_name():
        continue
    lines.append(f"template={obj.get_name()}")
    for prop in sorted(dir(obj)):
        if prop.startswith("_"):
            continue
        if "clip" in prop.lower() or "near" in prop.lower():
            try:
                lines.append(f"  {prop}={obj.get_editor_property(prop)!r}")
            except Exception:
                pass
OUT.write_text("\n".join(lines))
