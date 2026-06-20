"""Dump IA_Look consumption flags and compare both IMC look mappings."""

import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_ia_look_consume.log")


def log(msg: str) -> None:
    with open(LOG, "a") as f:
        f.write(msg + "\n")
    unreal.log(f"[probe_ia_look_consume] {msg}")


def dump_imc(path: str) -> None:
    imc = unreal.load_asset(path)
    dkm = imc.get_editor_property("default_key_mappings")
    for m in dkm.get_editor_property("mappings"):
        action = m.get_editor_property("action")
        if not action or action.get_name() != "IA_Look":
            continue
        key = m.get_editor_property("key").get_editor_property("key_name")
        log(f"{path} IA_Look key={key}")
        for mod in m.get_editor_property("modifiers"):
            cls = mod.get_class().get_name()
            extra = ""
            if "Scalar" in cls:
                extra = f" scalar={mod.get_editor_property('scalar')}"
            log(f"  {cls}{extra}")


def main() -> None:
    open(LOG, "w").close()
    ia = unreal.load_asset("/Game/BodycamFPSKIT/Input/Actions/IA_Look.IA_Look")
    log(f"IA_Look.bConsumeInput={ia.get_editor_property('bConsumeInput')}")
    log(
        f"IA_Look.bConsumesActionAndAxisMappings="
        f"{ia.get_editor_property('bConsumesActionAndAxisMappings')}"
    )
    log(
        f"IA_Look.TriggerEventsThatConsumeLegacyKeys="
        f"{ia.get_editor_property('TriggerEventsThatConsumeLegacyKeys')}"
    )
    dump_imc("/Game/BodycamFPSKIT/Input/IMC_Player.IMC_Player")
    dump_imc("/Game/BodycamFPSKIT/Input/IMC_Player_Default.IMC_Player_Default")
    log("done")


if __name__ == "__main__":
    main()
