"""Dump all post-process and camera-related settings."""
import unreal
from pathlib import Path

MAP = "/Game/BodycamFPSKIT/Maps/Map_Test"
LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/dump_pp_full.log")
lines = []


def p(msg):
    lines.append(str(msg))


def dump_obj(obj, prefix=""):
    for name in sorted(dir(obj)):
        if name.startswith("_"):
            continue
        if not any(k in name.lower() for k in ("exposure", "bright", "local", "physical", "vignette", "blend", "ev100", "bias", "adapt")):
            continue
        try:
            p(f"{prefix}{name}={obj.get_editor_property(name)}")
        except Exception:
            pass


unreal.EditorLoadingAndSavingUtils.load_map(MAP)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PostProcessVolume.static_class()):
    p(f"=== {actor.get_name()} unbound={actor.get_editor_property('unbound')} ===")
    dump_obj(actor.settings, "vol.")

for mat_path in (
    "/Game/BodycamFPSKIT/Blueprints/Camera/Materials/M_Vignette",
    "/Game/BodycamFPSKIT/Blueprints/Camera/Materials/M_FishEyeLens",
):
    mat = unreal.load_asset(mat_path)
    if mat:
        try:
            p(f"{mat_path} blend={mat.get_editor_property('blend_mode')}")
        except Exception as exc:
            p(f"{mat_path} blend err {exc}")

LOG.write_text("\n".join(lines))
