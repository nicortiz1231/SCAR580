"""Probe multiplayer game mode + map wiring."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_ar_multiplayer_runtime.log")
lines = []


def p(msg):
    lines.append(str(msg))
    unreal.log(str(msg))


def dump_gm(path):
    bp = unreal.load_asset(path)
    if not bp:
        p(f"MISSING {path}")
        return
    cdo = unreal.get_default_object(bp.generated_class())
    p(f"=== {path} ===")
    p(f"  parent={bp.get_editor_property('parent_class')}")
    for prop in ("default_pawn_class", "player_controller_class", "hud_class"):
        val = cdo.get_editor_property(prop)
        p(f"  {prop}={val.get_path_name() if val else None}")


dump_gm("/Game/SCAR580/Blueprints/GameModes/GM_SCAR_AR_Multiplayer.GM_SCAR_AR_Multiplayer")
dump_gm("/Game/SCAR580/Blueprints/GameModes/GM_SCAR_AR.GM_SCAR_AR")

MAP = "/Game/SCAR580/Maps/Map_AR"
unreal.EditorLoadingAndSavingUtils.load_map(MAP)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
ws = world.get_world_settings()
p(f"Map_AR default_game_mode={ws.get_editor_property('default_game_mode').get_path_name()}")

OUT.write_text("\n".join(lines))
