"""List CameraComponent properties for near clip in UE 5.8."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_cam_props.log")
lines = []

cdo = unreal.get_default_object(unreal.CameraComponent.static_class())
for prop in sorted(dir(cdo)):
    if prop.startswith("_"):
        continue
    lower = prop.lower()
    if not any(k in lower for k in ("clip", "near", "custom", "plane")):
        continue
    try:
        lines.append(f"CDO.{prop}={cdo.get_editor_property(prop)!r}")
    except Exception as exc:
        lines.append(f"CDO.{prop} ERR {exc}")

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
for handle in sds.k2_gather_subobject_data_for_blueprint(bp):
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(
        unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    )
    if not obj or "FirstPersonCamera" not in obj.get_name():
        continue
    lines.append(f"=== {obj.get_name()} ===")
    for prop in sorted(dir(obj)):
        if prop.startswith("_"):
            continue
        lower = prop.lower()
        if not any(k in lower for k in ("clip", "near", "custom", "plane", "field")):
            continue
        try:
            lines.append(f"  {prop}={obj.get_editor_property(prop)!r}")
        except Exception as exc:
            lines.append(f"  {prop} ERR {exc}")

# spawn SetFieldOfView as control
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(bp)
)
node = editor.add_call_function_node("/Script/Engine.CameraComponent:SetFieldOfView")
lines.append(f"SetFieldOfView spawn={node!r}")

OUT.write_text("\n".join(lines))
