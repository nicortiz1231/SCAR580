"""List all sniper components and attachment sockets."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sniper_components.log")
lines = []

SNIPER = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper"
sniper_bp = unreal.load_asset(SNIPER)
cdo = unreal.get_default_object(sniper_bp.generated_class())

lines.append("=== CDO properties with Sight/Scope ===")
for name in sorted(dir(cdo)):
    if name.startswith("_"):
        continue
    if not any(k in name for k in ("Sight", "Scope", "Optic", "Mesh")):
        continue
    try:
        val = cdo.get_editor_property(name)
        if hasattr(val, "get_name"):
            lines.append(f"  {name}={val.get_name()}")
        else:
            lines.append(f"  {name}={val!r}")
    except Exception:
        pass

lines.append("=== StaticMeshComponents ===")
try:
    comps = cdo.get_components_by_class(unreal.StaticMeshComponent.static_class())
    for comp in comps:
        sm = comp.get_editor_property("static_mesh")
        parent = comp.get_attach_parent()
        socket = comp.get_attach_socket_name()
        lines.append(
            f"  {comp.get_name()} mesh={sm.get_name() if sm else None} "
            f"parent={parent.get_name() if parent else None} socket={socket} "
            f"visible={comp.get_editor_property('visible')} hidden={comp.get_editor_property('hidden_in_game')}"
        )
except Exception as exc:
    lines.append(f"ERR {exc}")

sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
lines.append("=== Subobject handles ===")
for handle in sds.k2_gather_subobject_data_for_blueprint(sniper_bp):
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
    if not obj:
        continue
    if "Sight" in obj.get_name() or "Scope" in obj.get_name() or "Optic" in obj.get_name():
        sm = None
        try:
            sm = obj.get_editor_property("static_mesh")
        except Exception:
            pass
        lines.append(f"  {obj.get_name()} class={obj.get_class().get_name()} mesh={sm.get_name() if sm else None}")

OUT.write_text("\n".join(lines))
