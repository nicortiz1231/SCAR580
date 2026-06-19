"""List all IA_Look mappings with key names and modifiers."""

import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_imc_look.log")


def log(msg: str) -> None:
    with open(LOG, "a") as f:
        f.write(msg + "\n")


def main() -> None:
    with open(LOG, "a") as f:
        f.write("\n--- all IA_Look mappings ---\n")

    imc = unreal.load_asset("/Game/BodycamFPSKIT/Input/IMC_Player_Default.IMC_Player_Default")
    dkm = imc.get_editor_property("default_key_mappings")
    for i, m in enumerate(dkm.get_editor_property("mappings")):
        action = m.get_editor_property("action")
        aname = action.get_name() if action else None
        if aname != "IA_Look":
            continue
        key = m.get_editor_property("key")
        key_name = key.get_editor_property("key_name")
        log(f"[{i}] key={key_name}")
        for mod in m.get_editor_property("modifiers"):
            cls = mod.get_class().get_name()
            extra = ""
            if "Scalar" in cls:
                extra = f" scalar={mod.get_editor_property('scalar')}"
            if "Negate" in cls:
                extra += f" negate y={mod.get_editor_property('y')}"
            if "DeadZone" in cls:
                extra += f" dz lower={mod.get_editor_property('lower_threshold')}"
            if "Swizzle" in cls:
                extra += f" swizzle={mod.get_editor_property('order')}"
            log(f"    {cls}{extra}")


if __name__ == "__main__":
    main()
