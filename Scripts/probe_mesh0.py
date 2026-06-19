import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_mesh0.log")
lines = []


def p(msg):
    lines.append(str(msg))


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
cdo = unreal.get_default_object(bp.generated_class())
for comp in cdo.get_components_by_class(unreal.SkeletalMeshComponent.static_class()):
    p(f"comp={comp.get_name()}")
    try:
        mesh = comp.get_skeletal_mesh_asset()
        p(f"  mesh={mesh.get_path_name() if mesh else None}")
    except Exception as exc:
        p(f"  mesh err {exc}")
    for prop in ("hidden_in_game", "visible", "only_owner_see", "owner_no_see"):
        try:
            p(f"  {prop}={comp.get_editor_property(prop)}")
        except Exception as exc:
            p(f"  {prop} err {exc}")

LOG.write_text("\n".join(lines))
