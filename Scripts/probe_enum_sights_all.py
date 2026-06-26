import unreal
from pathlib import Path

lines = []
# load enum via sniper pickup sight property type
pickup = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Pickup_Sniper.BP_Weapon_Pickup_Sniper")
cdo = unreal.get_default_object(pickup.generated_class())
sight = cdo.get_editor_property("Item Data AttachmentsSight")
ec = type(sight)
lines.append(f"enum class={ec}")
for name in dir(ec):
    if name.isupper() or name.startswith("NEW"):
        try:
            v = getattr(ec, name)
            lines.append(f"  {name} = {v}")
        except Exception:
            pass

# try load enum asset directly
for path in (
    "/Game/BodycamFPSKIT/Blueprints/Enums/ENUM_Sights.ENUM_Sights",
    "/Game/BodycamFPSKIT/Blueprints/Enums/NUM_Sights.NUM_Sights",
):
    asset = unreal.load_asset(path)
    lines.append(f"asset {path} -> {asset}")

Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_enum_sights_all.log").write_text("\n".join(lines))
