import unreal
from pathlib import Path
OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_event_override.log")
lines = []
sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
fn = unreal.BlueprintEditorLibrary.add_event_override
lines.append(f"add_event_override={fn}")
try:
    help_text = fn.__doc__
    lines.append(f"doc={help_text}")
except Exception:
    pass
try:
    graph = unreal.BlueprintEditorLibrary.add_event_override(sniper, "SpawnAttachments")
    lines.append(f"result={graph}")
except Exception as exc:
    lines.append(f"call ERR {exc}")
OUT.write_text("\n".join(lines))
