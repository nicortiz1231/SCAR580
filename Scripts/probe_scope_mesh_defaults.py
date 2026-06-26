"""Check ScopeSightMesh on pistol vs sniper."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_scope_mesh_defaults.log")
lines = []

for path in (
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Pistol/BP_Weapon_Pistol.BP_Weapon_Pistol",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/AmericanRifle/BP_Weapon_AmericanRifle.BP_Weapon_AmericanRifle",
):
    bp = unreal.load_asset(path)
    cdo = unreal.get_default_object(bp.generated_class())
    scope = cdo.get_editor_property("ScopeSightMesh")
    optic = cdo.get_editor_property("OpticSightMesh")
    lines.append(
        f"{path.split('/')[-1]} ScopeSightMesh={scope.get_name() if scope else None} "
        f"OpticSightMesh={optic.get_name() if optic else None}"
    )

OUT.write_text("\n".join(lines))
