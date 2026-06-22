import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_touch_control_props.log")
if LOG.exists():
    LOG.unlink()

c = unreal.TouchInputControl()
for prop in sorted(dir(c)):
    if prop.startswith("_"):
        continue
    try:
        val = c.get_editor_property(prop) if hasattr(c, "get_editor_property") else None
    except Exception:
        val = "?"
    LOG.write_text(LOG.read_text() + f"{prop}: {val}\n" if LOG.exists() else f"{prop}: {val}\n")
