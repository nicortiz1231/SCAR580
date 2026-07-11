"""Probe UI_WeaponModding UMG hierarchy and slot layout."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_modding_widget_layout.log")
lines = []

WBP = "/Game/BodycamFPSKIT/Blueprints/Widgets/UI_WeaponModding.UI_WeaponModding"
wbp = unreal.load_asset(f"{WBP}.UI_WeaponModding")
cls = wbp.generated_class()
cdo = unreal.get_default_object(cls)

lines.append(f"class={cls.get_name()}")


def describe_widget(widget, depth=0):
    if not widget:
        return
    indent = "  " * depth
    wcls = widget.get_class().get_name()
    wname = widget.get_name()
    lines.append(f"{indent}{wname} ({wcls})")

    # geometry / transform hints
    for prop in ("RenderTransform", "RenderTransformPivot", "RenderOpacity", "Visibility"):
        try:
            lines.append(f"{indent}  {prop}={widget.get_editor_property(prop)!r}")
        except Exception:
            pass

    if isinstance(widget, unreal.PanelWidget):
        for i in range(widget.get_children_count()):
            child = widget.get_child_at(i)
            describe_widget(child, depth + 1)
    elif isinstance(widget, unreal.UserWidget):
        try:
            wt = widget.widget_tree
            if wt:
                root = wt.root_widget
                if root:
                    lines.append(f"{indent}  [UserWidget root]")
                    describe_widget(root, depth + 1)
        except Exception as exc:
            lines.append(f"{indent}  widget_tree ERR {exc}")


describe_widget(cdo)

# Named bindings from blueprint
for prop_name in sorted(dir(cdo)):
    if prop_name.startswith("_"):
        continue
    try:
        val = cdo.get_editor_property(prop_name)
    except Exception:
        continue
    if val is None:
        continue
    vcls = val.get_class().get_name() if hasattr(val, "get_class") else type(val).__name__
    if any(k in prop_name.lower() for k in ("sight", "laser", "muzzle", "grip", "inspect", "horizontal", "vertical", "canvas", "overlay", "box", "scale")):
        lines.append(f"PROP {prop_name} -> {vcls} {val!r}")

# Graph nodes related to layout / scale / viewport
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(wbp))
layout_kw = ("Scale", "Viewport", "Orientation", "Size", "Render", "Slot", "Padding", "Horizontal", "Vertical", "Wrap", "Grid")
lines.append("\n=== layout-related graph nodes ===")
for node in eg.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    if any(k.lower() in title.lower() for k in layout_kw):
        lines.append(f"  {node.get_name()} | {title}")

OUT.write_text("\n".join(lines))
