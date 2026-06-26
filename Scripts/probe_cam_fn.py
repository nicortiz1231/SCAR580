import unreal
from pathlib import Path
OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_cam_fn.log")
lines = []
for fn in (
    "/Script/Engine.CameraComponent:SetNearClipPlane",
    "/Script/Engine.CameraComponent:SetFieldOfView",
    "/Script/Engine.PlayerCameraManager:SetManualCameraFade",
):
    lines.append(f"{fn} -> {unreal.load_object(None, fn)}")
cdo = unreal.get_default_object(unreal.CameraComponent.static_class())
if hasattr(cdo, "get_property_names"):
    for name in cdo.get_property_names():
        if "clip" in name.lower() or "near" in name.lower():
            lines.append(f"prop {name}={cdo.get_editor_property(name)!r}")
OUT.write_text("\n".join(lines))
