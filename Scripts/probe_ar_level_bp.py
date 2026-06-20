import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_ar_level_bp.log")
lines = []

def p(msg):
    lines.append(str(msg))
    unreal.log(str(msg))

for path in (
    "/Game/HandheldAR/Maps/HandheldARBlankMap",
    "/Game/HandheldAR/Maps/HandheldARBlankMap.HandheldARBlankMap",
):
    asset = unreal.load_asset(path)
    p(f"{path} -> {asset}")

# Try to find HandheldARBlankMap blueprint class
for asset_path in unreal.EditorAssetLibrary.list_assets("/Game/HandheldAR", recursive=True):
    if "HandheldARBlankMap" in asset_path and not asset_path.endswith(".HandheldARBlankMap"):
        p(f"asset: {asset_path}")

cls = unreal.load_class(None, "/Game/HandheldAR/Maps/HandheldARBlankMap.HandheldARBlankMap_C")
p(f"level bp class={cls}")
if cls:
    cdo = unreal.get_default_object(cls)
    p(f"cdo={cdo}")
    for prop in dir(cdo):
        if "session" in prop.lower() or "config" in prop.lower() or "ar" in prop.lower():
            try:
                p(f"  {prop}={cdo.get_editor_property(prop)}")
            except Exception as exc:
                p(f"  {prop} ERR {exc}")

config = unreal.load_asset("/Game/HandheldAR/D_ARSessionConfig")
if config:
    for prop in (
        "b_enable_automatic_camera_overlay",
        "bEnableAutomaticCameraOverlay",
        "b_enable_automatic_camera_tracking",
        "bEnableAutomaticCameraTracking",
        "b_horizontal_plane_detection",
        "bHorizontalPlaneDetection",
        "b_vertical_plane_detection",
        "bEnableAutoFocus",
    ):
        try:
            p(f"config {prop}={config.get_editor_property(prop)}")
        except Exception as exc:
            p(f"config {prop} ERR")

OUT.write_text("\n".join(lines))
