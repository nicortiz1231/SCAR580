"""Probe WidgetBlueprint widget tree access APIs."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_modding_widget_tree_api.log")
lines = []

wbp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Widgets/UI_WeaponModding.UI_WeaponModding")
lines.append(f"wbp={wbp} class={wbp.get_class().get_name()}")

for prop in dir(wbp):
    if any(k in prop.lower() for k in ("widget", "tree", "root", "designer")):
        lines.append(f"  attr {prop}")

for method in ("get_widget_tree", "widget_tree", "get_editor_property"):
    try:
        val = getattr(wbp, method)
        lines.append(f"method {method}={val}")
    except Exception as exc:
        lines.append(f"method {method} ERR {exc}")

# try editor properties
for name in (
    "WidgetTree", "widget_tree", "BlueprintType", "ParentClass",
    "SimpleConstructionScript", "GeneratedClass",
):
    try:
        val = wbp.get_editor_property(name)
        lines.append(f"prop {name}={val!r}")
    except Exception as exc:
        lines.append(f"prop {name} ERR {exc}")

# WidgetTree from generated class default subobjects
cls = wbp.generated_class()
cdo = unreal.get_default_object(cls)
for name in ("Sight", "Laser", "Muzzle", "GRIP", "HorizontalBox", "CanvasPanel", "Overlay", "ScaleBox", "SizeBox"):
    try:
        val = cdo.get_editor_property(name)
        lines.append(f"cdo.{name}={val!r} class={val.get_class().get_name() if val else None}")
    except Exception as exc:
        lines.append(f"cdo.{name} ERR {exc}")

# list known widget bindings on cdo
lines.append("\n=== cdo widget bindings ===")
for name in sorted(dir(cdo)):
    if name.startswith("_"):
        continue
    if not any(k in name.lower() for k in ("sight", "laser", "muzzle", "grip", "box", "canvas", "overlay", "text", "inspect", "scale", "size")):
        continue
    try:
        val = cdo.get_editor_property(name)
        vcls = val.get_class().get_name() if val and hasattr(val, "get_class") else type(val).__name__
        lines.append(f"  {name} -> {vcls}")
    except Exception as exc:
        lines.append(f"  {name} ERR {exc}")

OUT.write_text("\n".join(lines))
