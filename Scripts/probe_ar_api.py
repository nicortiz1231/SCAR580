import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_ar_api.log")
lines = []

def p(msg):
    lines.append(str(msg))
    unreal.log(str(msg))

for name in sorted(dir(unreal)):
    if "AR" in name or "Plane" in name:
        p(name)

config = unreal.load_asset("/Game/HandheldAR/D_ARSessionConfig")
if config:
    p(f"config class={config.get_class().get_name()}")
    for prop in (
        "session_type",
        "plane_detection_mode",
        "plane_detection_method",
        "b_generate_mesh_data_from_tracked_geometry",
        "b_enable_auto_focus",
        "default_tracking_configuration",
    ):
        try:
            p(f"{prop}={config.get_editor_property(prop)}")
        except Exception as exc:
            p(f"{prop} ERR {exc}")

gm = unreal.load_asset("/Game/HandheldAR/Blueprints/GameFramework/BP_ARGameMode.BP_ARGameMode")
if gm:
    cdo = unreal.get_default_object(gm.generated_class())
    for prop in (
        "default_pawn_class",
        "player_controller_class",
        "default_session_config",
        "session_config",
    ):
        try:
            p(f"BP_ARGameMode.{prop}={cdo.get_editor_property(prop)}")
        except Exception as exc:
            p(f"BP_ARGameMode.{prop} ERR {exc}")

OUT.write_text("\n".join(lines))
