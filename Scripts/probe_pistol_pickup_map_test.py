"""Inspect Map_Test pistol pickup placement for AR parity."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_pistol_pickup_map_test.log")
lines = []

unreal.EditorLoadingAndSavingUtils.load_map("/Game/BodycamFPSKIT/Maps/Map_Test")
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor.static_class()):
    cls = actor.get_class().get_name()
    if "Pistol" not in cls and "Pistol" not in actor.get_actor_label():
        continue
    loc = actor.get_actor_location()
    rot = actor.get_actor_rotation()
    lines.append(f"{actor.get_actor_label()} ({cls})")
    lines.append(f"  loc={loc.x:.2f},{loc.y:.2f},{loc.z:.2f}")
    lines.append(f"  rot={rot.pitch:.2f},{rot.yaw:.2f},{rot.roll:.2f}")
    lines.append(f"  hidden_in_game={actor.is_hidden()}")

for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PlayerStart.static_class()):
    loc = actor.get_actor_location()
    rot = actor.get_actor_rotation()
    lines.append(f"PlayerStart loc={loc.x:.2f},{loc.y:.2f},{loc.z:.2f} rot={rot.pitch:.2f},{rot.yaw:.2f},{rot.roll:.2f}")

OUT.write_text("\n".join(lines))
