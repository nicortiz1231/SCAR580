import unreal
from pathlib import Path
OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_camera_nearclip2.log")
lines = []
cam_class = unreal.CameraComponent.static_class()
cdo = unreal.get_default_object(cam_class)
lines.append(f"CameraComponent CDO={cdo}")
for prop in sorted(dir(cdo)):
    if prop.startswith("_"):
        continue
    lower = prop.lower()
    if "clip" in lower or "near" in lower:
        try:
            lines.append(f"  {prop}={cdo.get_editor_property(prop)!r}")
        except Exception as exc:
            lines.append(f"  {prop} ERR {exc}")

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
for handle in sds.k2_gather_subobject_data_for_blueprint(bp):
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle))
    if not obj or "FirstPersonCamera" not in obj.get_name():
        continue
    for prop in ("NearClipPlane",):
        try:
            lines.append(f"template {prop}={obj.get_editor_property(prop)!r}")
            obj.set_editor_property(prop, 2.5)
            lines.append(f"template after set={obj.get_editor_property(prop)!r}")
        except Exception as exc:
            lines.append(f"template {prop} ERR {exc}")

# DT props
dt = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/DT_SniperAnimationValues.DT_SniperAnimationValues")
lines.append(f"DT={dt}")
for prop in sorted(dir(dt)):
    if prop.startswith("_"):
        continue
    try:
        val = dt.get_editor_property(prop)
        if val is not None and val != "" and val is not False:
            lines.append(f"  DT.{prop}={val!r}")
    except Exception:
        pass
OUT.write_text("\n".join(lines))
