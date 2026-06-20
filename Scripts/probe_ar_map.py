import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_ar_map.log")
lines = []

def p(msg):
    lines.append(str(msg))
    unreal.log(str(msg))

MAP = "/Game/HandheldAR/Maps/HandheldARBlankMap"
unreal.EditorLoadingAndSavingUtils.load_map(MAP)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor.static_class()):
    cls = actor.get_class().get_name()
    if cls in ("Actor", "WorldSettings", "DefaultPhysicsVolume", "GameplayDebuggerPlayerManager", "AbstractNavData"):
        continue
    p(f"{actor.get_name()} :: {cls}")

config = unreal.load_asset("/Game/HandheldAR/D_ARSessionConfig")
if config:
    for prop in sorted([x for x in dir(config) if not x.startswith("_")]):
        pass
    # dump editable props via get_editor_property attempts on common names
    candidates = [
        "session_type",
        "world_alignment",
        "plane_detection_mode",
        "enabled_session_tracking_features",
        "bEnableAutoFocus",
        "bGenerateMeshDataFromTrackedGeometry",
        "bUseAutomaticCameraOverlay",
        "bUseAutomaticCameraOverlayRendering",
        "bRenderSceneDepth",
    ]
    for prop in candidates:
        try:
            p(f"D_ARSessionConfig.{prop}={config.get_editor_property(prop)}")
        except Exception as exc:
            p(f"D_ARSessionConfig.{prop} ERR")

gm = unreal.load_asset("/Game/HandheldAR/Blueprints/GameFramework/BP_ARGameMode.BP_ARGameMode")
cdo = unreal.get_default_object(gm.generated_class())
for prop in dir(cdo):
    if "session" in prop.lower() or "pawn" in prop.lower() or "controller" in prop.lower():
        try:
            p(f"GM.{prop}={cdo.get_editor_property(prop)}")
        except Exception:
            pass

OUT.write_text("\n".join(lines))
