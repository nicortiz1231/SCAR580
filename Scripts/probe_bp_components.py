import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_bp_components.log")
lines = []

def p(msg):
    lines.append(str(msg))
    unreal.log(str(msg))

BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter"
bp = unreal.load_asset(BP)

for fn in sorted(dir(unreal.BlueprintEditorLibrary)):
    if "component" in fn.lower() or "subobject" in fn.lower():
        p(f"BEL.{fn}")

names = [
    "CameraFPS",
    "FirstPersonCamera",
    "CharacterMesh",
    "CharacterMesh0",
    "AR_KeyLight",
    "AR_FillLight",
    "WeaponLight",
    "FillLight_Back",
    "FillLight_Top",
    "AC_BodycamCamera",
]
for name in names:
    try:
        comp = unreal.BlueprintEditorLibrary.get_component_template(bp, name)
    except Exception as exc:
        p(f"{name}: ERR {exc}")
        continue
    if not comp:
        p(f"{name}: missing")
        continue
    cls = comp.get_class().get_name()
    p(f"{name}: {cls}")
    for prop in (
        "visible",
        "b_visible",
        "hidden_in_game",
        "b_hidden_in_game",
        "intensity",
        "Intensity",
        "post_process_blend_weight",
        "cast_shadow",
        "b_cast_shadow",
    ):
        try:
            p(f"  {prop}={comp.get_editor_property(prop)}")
        except Exception:
            pass
    if "CameraComponent" in cls:
        try:
            settings = comp.post_process_settings
            blendables = settings.weighted_blendables
            p(f"  blendables={len(blendables.array)}")
        except Exception as exc:
            p(f"  blendables ERR {exc}")

OUT.write_text("\n".join(lines))
