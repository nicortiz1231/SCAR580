import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_imc_scalar.log")
open(LOG, "w").close()

imc = unreal.load_asset("/Game/BodycamFPSKIT/Input/IMC_Player.IMC_Player")
dkm = imc.get_editor_property("default_key_mappings")
for m in dkm.get_editor_property("mappings"):
    action = m.get_editor_property("action")
    if not action or action.get_name() != "IA_Look":
        continue
    key = m.get_editor_property("key").get_editor_property("key_name")
    if str(key) != "Mouse2D":
        continue
    mods = m.get_editor_property("modifiers")
    with open(LOG, "a") as f:
        f.write(f"modifier count={len(mods)}\n")
        for i, mod in enumerate(mods):
            cls = mod.get_class().get_name()
            line = f"[{i}] {cls}"
            if "Scalar" in cls:
                line += f" scalar={mod.get_editor_property('scalar')}"
            if "Negate" in cls:
                line += f" negate_y={mod.get_editor_property('y')}"
            f.write(line + "\n")
            unreal.log(line)
