"""Set OpticSight mesh on sniper CDO directly."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_sniper_optic_direct.log")
lines = []

sniper_bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
cdo = unreal.get_default_object(sniper_bp.generated_class())
scope = unreal.load_asset("/Game/BodycamFPSKIT/Demo/Meshes/SM_4xScopeForSniper.SM_4xScopeForSniper")

for name in ("OpticSight", "FrontSight", "RearSight"):
    try:
        comp = cdo.get_editor_property(name)
        lines.append(f"{name}={comp}")
        if name == "OpticSight" and comp:
            comp.set_editor_property("static_mesh", scope)
            lines.append(f"set static_mesh on {name}")
    except Exception as exc:
        lines.append(f"{name} ERR {exc}")

# all components
try:
    comps = cdo.get_components_by_class(unreal.StaticMeshComponent.static_class())
    lines.append(f"static comps count={len(comps)}")
    for comp in comps:
        if "Optic" in comp.get_name():
            comp.set_editor_property("static_mesh", scope)
            lines.append(f"set on component {comp.get_name()}")
except Exception as exc:
    lines.append(f"comps ERR {exc}")

sniper_bp.modify()
unreal.BlueprintEditorLibrary.compile_blueprint(sniper_bp)
unreal.EditorAssetLibrary.save_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper",
    only_if_is_dirty=False,
)

cdo2 = unreal.get_default_object(sniper_bp.generated_class())
try:
    comp = cdo2.get_editor_property("OpticSight")
    sm = comp.get_editor_property("static_mesh")
    lines.append(f"after save OpticSight mesh={sm.get_name() if sm else None}")
except Exception as exc:
    lines.append(f"verify ERR {exc}")

OUT.write_text("\n".join(lines))
