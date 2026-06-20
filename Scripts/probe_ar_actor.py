import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_ar_actor.log")
lines = []

def p(msg):
    lines.append(str(msg))
    unreal.log(str(msg))

MAP = "/Game/HandheldAR/Maps/HandheldARBlankMap"
unreal.EditorLoadingAndSavingUtils.load_map(MAP)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

actor = None
for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor.static_class()):
    if a.get_class().get_name() == "HandheldARBlankMap_C":
        actor = a
        break

p(f"actor={actor}")
if actor:
    comps = actor.get_components_by_class(unreal.ActorComponent.static_class())
    for comp in comps:
        p(f"  comp {comp.get_name()} :: {comp.get_class().get_name()}")
        for prop in ("session_config", "default_session_config", "config", "ar_session_config"):
            try:
                p(f"    {prop}={comp.get_editor_property(prop)}")
            except Exception:
                pass

# World settings
ws = world.get_world_settings()
for prop in dir(ws):
    if "ar" in prop.lower() or "session" in prop.lower():
        try:
            p(f"WorldSettings.{prop}={ws.get_editor_property(prop)}")
        except Exception:
            pass

# Load level script blueprint asset if exists
for path in unreal.EditorAssetLibrary.list_assets("/Game/HandheldAR", recursive=True):
    if "HandheldARBlankMap" in path:
        p(f"asset {path}")

OUT.write_text("\n".join(lines))
