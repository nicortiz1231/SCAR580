import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/verify_ar_setup.log")
lines = []

def p(msg):
    lines.append(str(msg))
    unreal.log(msg)

checks = [
    "/Game/SCAR580/Blueprints/GameModes/GM_SCAR_AR",
    "/Game/SCAR580/Maps/Map_AR",
    "/Game/HandheldAR/D_ARSessionConfig",
]

for path in checks:
    p(f"{path} exists={unreal.EditorAssetLibrary.does_asset_exist(path)}")

gm = unreal.load_asset("/Game/SCAR580/Blueprints/GameModes/GM_SCAR_AR.GM_SCAR_AR")
cdo = unreal.get_default_object(gm.generated_class())
p(f"GM pawn={cdo.get_editor_property('default_pawn_class').get_name()}")
p(f"GM pc={cdo.get_editor_property('player_controller_class').get_name()}")

cfg = unreal.load_asset("/Game/HandheldAR/D_ARSessionConfig")
p(f"overlay={cfg.get_editor_property('bEnableAutomaticCameraOverlay')}")
p(f"tracking={cfg.get_editor_property('bEnableAutomaticCameraTracking')}")

OUT.write_text("\n".join(lines))
