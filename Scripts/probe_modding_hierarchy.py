"""Walk widget parent chain from Sight combobox."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_modding_hierarchy.log")
lines = []

wbp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Widgets/UI_WeaponModding.UI_WeaponModding")
cls = wbp.generated_class()

world = unreal.EditorLevelLibrary.get_editor_world()
widget = unreal.WidgetBlueprintLibrary.create(world, cls)
if not widget:
    raise RuntimeError("create widget failed")

for name in ("Sight", "Laser", "Muzzle", "GRIP"):
    try:
        w = widget.get_widget_from_name(name)
    except Exception:
        w = None
    lines.append(f"\n=== {name} -> {w} ===")
    if not w:
        continue
    cur = w
    depth = 0
    while cur and depth < 12:
        cls_name = cur.get_class().get_name()
        lines.append(f"{'  '*depth}{cur.get_name()} ({cls_name})")
        try:
            cur = cur.get_parent()
        except Exception:
            break
        depth += 1

# dump VerticalBox / HorizontalBox tree under root
lines.append("\n=== panel tree ===")

def dump(w, depth=0):
    if not w or depth > 8:
        return
    cls_name = w.get_class().get_name()
    if cls_name in ("VerticalBox", "HorizontalBox", "CanvasPanel", "TextBlock", "ComboBoxString"):
        lines.append(f"{'  '*depth}{w.get_name()} ({cls_name})")
    if isinstance(w, unreal.PanelWidget):
        for i in range(w.get_children_count()):
            dump(w.get_child_at(i), depth + 1)

try:
    wt = widget.get_editor_property("widget_tree")
    dump(wt.get_editor_property("root_widget"))
except Exception as exc:
    lines.append(f"tree ERR {exc}")

OUT.write_text("\n".join(lines))
