"""Spawn a temporary BP_FPCharacter instance in the currently loaded editor
world to get REAL resolved component attachments (CDO templates don't
reliably report AttachParent for SCS-added components)."""
import unreal
from pathlib import Path

BP_ASSET = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter"
MAP_AR = "/Game/SCAR580/Maps/Map_AR"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_spawned_attachment.log")


def log(msg: str) -> None:
    with LOG_PATH.open("a") as f:
        f.write(str(msg) + "\n")
    unreal.log(f"[probe_spawned] {msg}")


if LOG_PATH.exists():
    LOG_PATH.unlink()

unreal.EditorLoadingAndSavingUtils.load_map(MAP_AR)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
if not world:
    raise RuntimeError("No editor world")

bp_class = unreal.load_asset(BP_ASSET).generated_class()
actor = unreal.EditorLevelLibrary.spawn_actor_from_class(bp_class, unreal.Vector(0, 0, 500))
if not actor:
    raise RuntimeError("Spawn failed")

log(f"Spawned {actor.get_name()}")

comps = actor.get_components_by_class(unreal.SceneComponent.static_class())
log(f"Total scene components: {len(comps)}")
for comp in comps:
    try:
        parent = comp.get_attach_parent()
        parent_name = parent.get_name() if parent else "None (root)"
    except Exception as exc:
        parent_name = f"ERR {exc}"
    try:
        socket = str(comp.get_attach_socket_name())
    except Exception:
        socket = "?"
    try:
        rel_loc = comp.get_editor_property("relative_location")
        rel_rot = comp.get_editor_property("relative_rotation")
    except Exception:
        rel_loc = rel_rot = None
    log(f"{comp.get_name()} ({comp.get_class().get_name()}) parent={parent_name} socket={socket} relLoc={rel_loc} relRot={rel_rot}")

unreal.EditorLevelLibrary.destroy_actor(actor)
log("DONE")
