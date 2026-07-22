import unreal
from pathlib import Path
LOG=Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_enemy_walkspeed.log")
bp=unreal.load_asset("/Game/FirstPersonHorrorKit/Blueprints/Enemy/BP_Enemy")
cdo=unreal.get_default_object(bp.generated_class())
move=cdo.get_editor_property("character_movement") if hasattr(cdo,"get_editor_property") else None
lines=[]
def w(m):
    lines.append(str(m)); unreal.log(str(m))
w(f"cdo={cdo}")
# CharacterMovement is a component on the CDO
try:
    cmc=cdo.get_component_by_class(unreal.CharacterMovementComponent)
    w(f"cmc={cmc}")
    if cmc:
        w(f"MaxWalkSpeed={cmc.max_walk_speed}")
        w(f"MaxAcceleration={cmc.max_acceleration}")
except Exception as e:
    w(f"comp err {e}")
# Also dump via exported properties
for name in ("max_walk_speed","MaxWalkSpeed"):
    try:
        w(f"cdo.{name}={cdo.get_editor_property(name)}")
    except Exception as e:
        w(f"cdo.{name} fail {e}")
LOG.write_text("\n".join(lines)+"\n")
