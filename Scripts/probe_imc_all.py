"""Dump IA_Look mappings from both IMC_Player and IMC_Player_Default."""

import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_imc_all.log")


def log(msg: str) -> None:
    with open(LOG, "a") as f:
        f.write(msg + "\n")
    unreal.log(f"[probe_imc_all] {msg}")


def dump_imc(path: str) -> None:
    imc = unreal.load_asset(path)
    if not imc:
        log(f"MISSING {path}")
        return
    log(f"=== {path} ===")
    dkm = imc.get_editor_property("default_key_mappings")
    mappings = dkm.get_editor_property("mappings")
    log(f"mappings={len(mappings)}")
    for i, m in enumerate(mappings):
        action = m.get_editor_property("action")
        aname = action.get_name() if action else None
        if aname != "IA_Look":
            continue
        key_name = m.get_editor_property("key").get_editor_property("key_name")
        log(f"  [{i}] IA_Look key={key_name}")
        for mod in m.get_editor_property("modifiers"):
            cls = mod.get_class().get_name()
            extra = ""
            if "Scalar" in cls:
                extra = f" scalar={mod.get_editor_property('scalar')}"
            if "Negate" in cls:
                extra += f" negate y={mod.get_editor_property('y')}"
            if "DeadZone" in cls:
                extra += f" dz={mod.get_editor_property('lower_threshold')}"
            if "Swizzle" in cls:
                extra += f" swizzle={mod.get_editor_property('order')}"
            log(f"    {cls}{extra}")


def main() -> None:
    open(LOG, "w").close()
    dump_imc("/Game/BodycamFPSKIT/Input/IMC_Player_Default.IMC_Player_Default")
    dump_imc("/Game/BodycamFPSKIT/Input/IMC_Player.IMC_Player")
    log("done")


if __name__ == "__main__":
    main()
