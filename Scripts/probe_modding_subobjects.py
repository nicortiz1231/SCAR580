"""Enumerate UI_WeaponModding designer widgets via subobject data."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_modding_subobjects.log")
lines = []

wbp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Widgets/UI_WeaponModding.UI_WeaponModding")
subsystem = unreal.get_editor_subsystem(unreal.SubobjectDataSubsystem)
handles = subsystem.k2_gather_subobject_data_for_blueprint(wbp)

lines.append(f"handles={len(handles)}")
for handle in handles:
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
    if not obj:
        continue
    name = obj.get_name()
    cls = obj.get_class().get_name()
    lines.append(f"  {name} | {cls}")
    if cls in ("TextBlock", "RichTextBlock", "CommonTextBlock"):
        try:
            text = obj.get_editor_property("text")
            lines.append(f"    text={text}")
        except Exception as exc:
            lines.append(f"    text ERR {exc}")

# Also try walking WidgetTree property on CDO via all_objects
cdo = unreal.get_default_object(wbp.generated_class())
for prop in ("WidgetTree",):
    try:
        lines.append(f"cdo {prop}={cdo.get_editor_property(prop)!r}")
    except Exception as exc:
        lines.append(f"cdo {prop} ERR {exc}")

OUT.write_text("\n".join(lines))
