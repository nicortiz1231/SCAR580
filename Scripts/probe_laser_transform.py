"""Read BP_Laser component transforms and weapon Laser mount offset."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_laser_transform.log")
lines = []

laser_bp = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Attachments/Laser/Blueprints/BP_Laser.BP_Laser"
)
if laser_bp:
    cls = laser_bp.generated_class()
    cdo = unreal.get_default_object(cls)
    lines.append(f"BP_Laser CDO class={cls.get_name()}")
    for comp in cdo.get_components_by_class(unreal.ActorComponent):
        name = comp.get_name()
        if any(k in name for k in ("Laser", "Beam", "Dot", "Mesh", "Flash")):
            lines.append(f"  component={name} class={comp.get_class().get_name()}")
            if hasattr(comp, "relative_location"):
                lines.append(f"    rel_loc={comp.relative_location}")
            if hasattr(comp, "relative_rotation"):
                lines.append(f"    rel_rot={comp.relative_rotation}")

weapon_bp = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase"
)
if weapon_bp:
    cls = weapon_bp.generated_class()
    cdo = unreal.get_default_object(cls)
    lines.append(f"\nAutomaticBase CDO")
    for comp in cdo.get_components_by_class(unreal.SceneComponent):
        name = comp.get_name()
        if "Laser" in name or "Item_Mesh" in name:
            lines.append(f"  {name} rel_loc={comp.relative_location} rel_rot={comp.relative_rotation}")

OUT.write_text("\n".join(lines))
unreal.log(f"[probe_laser_transform] wrote {OUT}")
