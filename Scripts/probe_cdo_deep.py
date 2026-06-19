"""Dump all CDO components on BP_FPCharacter and AC_BodycamCamera."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_cdo_deep.log")
lines = []


def p(msg):
    lines.append(str(msg))


def dump_actor_components(label, asset_path):
    bp = unreal.load_asset(asset_path)
    if not bp:
        p(f"{label}: missing {asset_path}")
        return
    cls = bp.generated_class()
    cdo = unreal.get_default_object(cls)
    p(f"{label}: class={cls.get_name()} BODYCAM={getattr(cdo, 'get_editor_property', lambda x: '?')('BODYCAM') if label.startswith('BP') else 'n/a'}")
    comps = cdo.get_components_by_class(unreal.ActorComponent.static_class())
    p(f"{label}: {len(comps)} components on CDO")
    for comp in comps:
        cls_name = comp.get_class().get_name()
        name = comp.get_name()
        p(f"  {name} ({cls_name})")
        if "SkeletalMesh" in cls_name:
            for prop in ("b_hidden_in_game", "hidden_in_game", "b_visible", "visible", "only_owner_see", "b_only_owner_see", "first_person_primitive_type"):
                try:
                    p(f"    {prop}={comp.get_editor_property(prop)}")
                except Exception as exc:
                    p(f"    {prop}: {exc}")
            try:
                mesh = comp.get_editor_property("skeletal_mesh")
                p(f"    skeletal_mesh={mesh.get_name() if mesh else None}")
            except Exception as exc:
                p(f"    skeletal_mesh: {exc}")
        if any(t in cls_name for t in ("PointLight", "SpotLight", "DirectionalLight")):
            for prop in ("b_hidden_in_game", "hidden_in_game", "b_visible", "visible", "intensity", "Intensity"):
                try:
                    p(f"    {prop}={comp.get_editor_property(prop)}")
                except Exception:
                    pass
        if "CameraComponent" in cls_name:
            for prop in ("post_process_blend_weight",):
                try:
                    p(f"    {prop}={comp.get_editor_property(prop)}")
                except Exception:
                    pass
            try:
                settings = comp.post_process_settings
                p(f"    blendables={len(settings.weighted_blendables.array)}")
                p(f"    auto_exposure_method={settings.get_editor_property('auto_exposure_method')}")
            except Exception as exc:
                p(f"    pp ERR {exc}")


dump_actor_components("BP_FPCharacter", "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
dump_actor_components("AC_BodycamCamera", "/Game/BodycamFPSKIT/Blueprints/Components/AC_BodycamCamera.AC_BodycamCamera")

LOG.write_text("\n".join(lines))
