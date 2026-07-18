"""Dump BP_GunShip Fire_L/Fire_R + 30MM spawn shake refs."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_fire_components.log")
lines = []

bp = unreal.load_asset("/Game/SCAR580/GunshipOps/AT_GS_C/Blueprints/BP_GunShip.BP_GunShip")
cdo = unreal.get_default_object(bp.generated_class())

for comp in cdo.get_components_by_class(unreal.ActorComponent):
    name = comp.get_name()
    if "Fire" in name or "Gun_Arrow" in name or name == "FPPCam":
        parent = comp.get_attach_parent().get_name() if comp.get_attach_parent() else "ROOT"
        cls = comp.get_class().get_name()
        rel_loc = getattr(comp, "relative_location", None)
        rel_rot = getattr(comp, "relative_rotation", None)
        lines.append(f"{name} | {cls} | parent={parent} | rel={rel_loc} | rot={rel_rot}")
        if isinstance(comp, unreal.ParticleSystemComponent):
            tmpl = comp.get_editor_property("template")
            lines.append(f"  template={tmpl.get_path_name() if tmpl else None}")

# BP_25MM projectile movement defaults
bullet = unreal.load_asset("/Game/SCAR580/GunshipOps/AT_GS_C/Blueprints/Weapons/Bullets/BP_25MM.BP_25MM")
bcdo = unreal.get_default_object(bullet.generated_class())
lines.append("\n=== BP_25MM defaults ===")
lines.append(f"actor_scale={bcdo.get_actor_scale3d()}")
for comp in bcdo.get_components_by_class(unreal.ActorComponent):
    cn = comp.get_class().get_name()
    lines.append(f"{comp.get_name()} :: {cn}")
    if "ProjectileMovement" in cn:
        for prop in ("initial_speed", "max_speed", "velocity", "b_is_homing_projectile",
                     "homing_acceleration_magnitude", "projectile_gravity_scale",
                     "b_rotation_follows_velocity"):
            try:
                lines.append(f"  {prop}={comp.get_editor_property(prop)}")
            except Exception as exc:
                lines.append(f"  {prop} ERR {exc}")
    if "StaticMesh" in cn:
        lines.append(f"  rel_scale={comp.relative_scale3d}")
        lines.append(f"  rel_rot={comp.relative_rotation}")

OUT.write_text("\n".join(lines))
print(OUT.read_text())
