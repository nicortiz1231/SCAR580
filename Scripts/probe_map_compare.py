"""Compare Map_Test vs Map_AR for weapon/loadout differences."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_map_compare.log")
lines = []


def p(msg):
    lines.append(str(msg))
    unreal.log(str(msg))


def dump_map(map_path, label):
    unreal.EditorLoadingAndSavingUtils.load_map(map_path)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    p(f"=== {label} ===")
    ws = world.get_world_settings()
    gm = ws.get_editor_property("default_game_mode")
    p(f"  game_mode={gm.get_name() if gm else None}")

    keywords = ("Weapon", "Pistol", "Pickup", "Player", "PostProcess", "Light", "Character", "Spawn")
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor.static_class()):
        cls = actor.get_class().get_name()
        label_name = actor.get_actor_label()
        if any(k in cls for k in keywords) or any(k in label_name for k in keywords):
            p(f"  actor {label_name} ({cls})")

    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PostProcessVolume.static_class()):
        settings = actor.settings
        p(f"  PPV unbound={actor.get_editor_property('unbound')} bias={settings.get_editor_property('auto_exposure_bias')}")


dump_map("/Game/BodycamFPSKIT/Maps/Map_Test", "Map_Test")
dump_map("/Game/SCAR580/Maps/Map_AR", "Map_AR")

# CDO weapon-related defaults
bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
cdo = unreal.get_default_object(bp.generated_class())
for prop in (
    "EquippedWeapon",
    "SelectedWeapon",
    "PrimarySlot",
    "SecondarySlot",
    "HandsSlot",
    "Equipped",
    "IsWeapon",
    "FOV_Base",
    "PickupWeaponSpawn",
):
    try:
        p(f"BP_FPCharacter.{prop}={cdo.get_editor_property(prop)}")
    except Exception as exc:
        p(f"BP_FPCharacter.{prop} ERR {exc}")

OUT.write_text("\n".join(lines))
