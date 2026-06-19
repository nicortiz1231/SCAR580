"""Probe all skeletal meshes and cameras on blueprint subobjects."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_all_meshes.log")
lines = []


def p(msg):
    lines.append(str(msg))


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
handles = sds.k2_gather_subobject_data_for_blueprint(bp)
seen = set()

for handle in handles:
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
    if not obj:
        continue
    oid = id(obj)
    if oid in seen:
        continue
    seen.add(oid)
    cn = obj.get_class().get_name()
    name = obj.get_name()
    if "SkeletalMesh" in cn:
        mesh = None
        try:
            mesh = obj.get_skeletal_mesh_asset()
        except Exception:
            pass
        p(f"MESH {name} class={cn} asset={mesh.get_path_name() if mesh else None}")
        for prop in ("hidden_in_game", "visible", "only_owner_see", "owner_no_see", "cast_hidden_shadow"):
            try:
                p(f"  {prop}={obj.get_editor_property(prop)}")
            except Exception as exc:
                p(f"  {prop}=ERR")
    if "Camera" in cn:
        settings = obj.post_process_settings
        p(
            f"CAM {name} method={settings.get_editor_property('auto_exposure_method')} "
            f"apply_physical={settings.get_editor_property('auto_exposure_apply_physical_camera_exposure')} "
            f"override_apply={settings.get_editor_property('override_auto_exposure_apply_physical_camera_exposure')}"
        )

LOG.write_text("\n".join(lines))
