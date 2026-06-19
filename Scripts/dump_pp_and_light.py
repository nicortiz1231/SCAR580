"""Dump PostProcessVolume and spawn diagnostic lights on Map_Test."""
import unreal
from pathlib import Path

MAP = "/Game/BodycamFPSKIT/Maps/Map_Test"
LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/dump_pp.log")
lines = []

def p(msg):
    lines.append(str(msg))

def dump_props(obj, prefix=""):
    cls = obj.get_class().get_name()
    for name in sorted(dir(obj)):
        if name.startswith("_"):
            continue
        if not any(k in name.lower() for k in ("exposure", "bright", "vignette", "local", "bias", "ev100", "light", "hidden", "visible", "intensity")):
            continue
        try:
            val = obj.get_editor_property(name)
            p(f"{prefix}{cls}.{name} = {val}")
        except Exception:
            pass

unreal.EditorLoadingAndSavingUtils.load_map(MAP)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PostProcessVolume.static_class()):
    p(f"PPV {actor.get_name()} unbound={actor.get_editor_property('unbound')}")
    dump_props(actor.settings, "settings.")

# Add a strong key light if missing - helps validate whether arms exist but are unlit.
existing = [a.get_name() for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.DirectionalLight.static_class())]
p(f"Directional lights: {existing}")

if not existing:
    light = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.DirectionalLight,
        unreal.Vector(0, 0, 300),
        unreal.Rotator(-45, 45, 0),
    )
    comp = light.get_component_by_class(unreal.DirectionalLightComponent.static_class())
    comp.set_editor_property("intensity", 3.0)
    comp.set_editor_property("light_color", unreal.LinearColor(1, 1, 1, 1))
    p("Spawned diagnostic DirectionalLight intensity=3")

unreal.EditorLoadingAndSavingUtils.save_map(unreal.load_asset(MAP), MAP)
LOG.write_text("\n".join(lines))
