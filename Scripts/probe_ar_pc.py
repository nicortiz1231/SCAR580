import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_ar_pc.log")
lines = []

def p(msg):
    lines.append(str(msg))
    unreal.log(str(msg))

for path, label in (
    ("/Game/HandheldAR/Blueprints/GameFramework/BP_ARPlayerController.BP_ARPlayerController", "ARPC"),
    ("/Game/SCAR580/Blueprints/GameModes/GM_SCAR_AR.GM_SCAR_AR", "GM"),
):
    bp = unreal.load_asset(path)
    cdo = unreal.get_default_object(bp.generated_class())
    p(f"{label} class={bp.generated_class().get_name()}")
    for prop in dir(cdo):
        lower = prop.lower()
        if "session" in lower or "ar" in lower:
            try:
                p(f"  {prop}={cdo.get_editor_property(prop)}")
            except Exception:
                pass

session = unreal.load_asset("/Game/HandheldAR/D_ARSessionConfig")
p(f"session overlay={session.get_editor_property('bEnableAutomaticCameraOverlay')}")

OUT.write_text("\n".join(lines))
