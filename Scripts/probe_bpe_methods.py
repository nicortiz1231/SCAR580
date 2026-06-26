"""List BlueprintGraphEditor methods for cast/branch."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_bpe_methods.log")
lines = []

for name in sorted(dir(unreal.BlueprintGraphEditor)):
    if any(k in name.lower() for k in ("cast", "branch", "function", "member", "variable", "custom")):
        lines.append(name)

OUT.write_text("\n".join(lines))
