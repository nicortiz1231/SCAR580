"""Dump bodycam camera and compare PP settings."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_bodycam_pp.log")
lines = []


def p(msg):
    lines.append(str(msg))


def dump_pp(settings, prefix):
    keys = (
        "auto_exposure_apply_physical_camera_exposure",
        "override_auto_exposure_apply_physical_camera_exposure",
        "auto_exposure_method",
        "auto_exposure_min_brightness",
        "auto_exposure_max_brightness",
        "local_exposure_method",
        "override_local_exposure_method",
        "local_exposure_detail_strength",
        "override_local_exposure_detail_strength",
    )
    for key in keys:
        try:
            p(f"{prefix}{key}={settings.get_editor_property(key)}")
        except Exception as exc:
            p(f"{prefix}{key}=ERR {exc}")


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Components/AC_BodycamCamera.AC_BodycamCamera")
cdo = unreal.get_default_object(bp.generated_class())
p(f"AC class={cdo.get_class().get_name()}")
for prop in ("post_process_settings", "post_process_blend_weight"):
    try:
        p(f"AC.{prop}={cdo.get_editor_property(prop)}")
    except Exception as exc:
        p(f"AC.{prop}=ERR {exc}")
try:
    dump_pp(cdo.post_process_settings, "AC.")
except Exception as exc:
    p(f"AC.pp ERR {exc}")

char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
char_cdo = unreal.get_default_object(char.generated_class())
p(f"BP BODYCAM={char_cdo.get_editor_property('BODYCAM')}")
for comp in char_cdo.get_components_by_class(unreal.ActorComponent.static_class()):
    cn = comp.get_class().get_name()
    if "Camera" in cn or "Light" in cn:
        p(f"comp {comp.get_name()} class={cn} hidden={getattr(comp, 'get_editor_property', lambda x: '?')('hidden_in_game')}")

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PostProcessVolume.static_class()):
    p(f"vol {actor.get_name()} unbound={actor.get_editor_property('unbound')}")
    dump_pp(actor.settings, "vol.")

for path in (
    "/Game/BodycamFPSKIT/Blueprints/Camera/Materials/M_Vignette",
    "/Game/BodycamFPSKIT/Blueprints/Camera/Materials/M_FishEyeLens",
):
    mat = unreal.load_asset(path)
    p(f"{path} blend={mat.get_editor_property('blend_mode')}")

LOG.write_text("\n".join(lines))
