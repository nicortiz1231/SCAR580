"""Find unreal Python APIs for widget blueprint editing."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_widget_bp_apis.log")
lines = []

for name in sorted(dir(unreal)):
    if any(k in name.lower() for k in ("widget", "umg", "slate")):
        if "Widget" in name or "UMG" in name:
            lines.append(name)

lines.append("\n=== WidgetBlueprint methods ===")
wbp_cls = unreal.WidgetBlueprint
for name in sorted(dir(wbp_cls)):
    if not name.startswith("_"):
        lines.append(name)

lines.append("\n=== EditorUtility / subsystem ===")
for name in sorted(dir(unreal)):
    if "WidgetBlueprint" in name or "UMGEditor" in name:
        lines.append(name)

OUT.write_text("\n".join(lines))
