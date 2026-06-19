import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_ac_bodycam2.log")
lines = []


def p(msg):
    lines.append(str(msg))


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Components/AC_BodycamCamera.AC_BodycamCamera")
cdo = unreal.get_default_object(bp.generated_class())
p(f"cdo={cdo.get_class().get_name()}")

for prop in (
    "Camera",
    "CameraComponent",
    "BodycamCamera",
    "PostProcessSettings",
    "VignetteMaterial",
    "FishEyeMaterial",
    "BODYCAM",
):
    try:
        p(f"{prop}={cdo.get_editor_property(prop)}")
    except Exception as exc:
        p(f"{prop}: {exc}")

# Dump all readable properties
for prop in dir(cdo):
    if prop.startswith("_") or prop.startswith("get_") or prop.startswith("set_"):
        continue
    if prop[0].islower():
        continue
    try:
        val = cdo.get_editor_property(prop)
        if val is not None and str(val) not in ("None", "False", "0", "0.0"):
            p(f"{prop}={val}")
    except Exception:
        pass

LOG.write_text("\n".join(lines))
