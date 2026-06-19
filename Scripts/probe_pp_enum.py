import unreal
from pathlib import Path
LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_pp_enum.log")
lines = [str(x) for x in dir(unreal.SceneTextureId) if "POST" in x or "INPUT" in x or "CUSTOM" in x]
lines += [str(x) for x in unreal.SceneTextureId]
LOG.write_text("\n".join(lines))
