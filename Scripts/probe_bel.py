import unreal
from pathlib import Path
OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_bel.log")
lines = [f"BEL.{fn}" for fn in sorted(dir(unreal.BlueprintEditorLibrary)) if not fn.startswith("_")]
OUT.write_text("\n".join(lines))
