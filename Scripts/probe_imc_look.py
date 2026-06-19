"""Dump IMC_Player_Default look mappings and modifier scalars."""

import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_imc_look.log")


def log(msg: str) -> None:
    with open(LOG, "a") as f:
        f.write(msg + "\n")
    unreal.log(f"[probe_imc_look] {msg}")


def dump_modifier(mod, indent="  ") -> None:
    cls = mod.get_class().get_name()
    log(f"{indent}modifier {mod.get_name()} ({cls})")
    if "Scalar" in cls:
        try:
            log(f"{indent}  scalar={mod.get_editor_property('scalar')}")
        except Exception as exc:
            log(f"{indent}  scalar err {exc}")
    if "Negate" in cls:
        try:
            log(f"{indent}  x={mod.get_editor_property('x')} y={mod.get_editor_property('y')} z={mod.get_editor_property('z')}")
        except Exception:
            pass
    if "Swizzle" in cls:
        try:
            log(f"{indent}  order={mod.get_editor_property('order')}")
        except Exception:
            pass
    if "DeadZone" in cls:
        try:
            log(f"{indent}  lower={mod.get_editor_property('lower_threshold')} upper={mod.get_editor_property('upper_threshold')}")
        except Exception:
            pass


def main() -> None:
    open(LOG, "w").close()
    imc = unreal.load_asset("/Game/BodycamFPSKIT/Input/IMC_Player_Default.IMC_Player_Default")
    if not imc:
        raise RuntimeError("missing IMC_Player_Default")

    for prop in ("default_key_mappings", "mappings"):
        try:
            val = imc.get_editor_property(prop)
            log(f"IMC.{prop} type={type(val).__name__}")
        except Exception as exc:
            log(f"IMC.{prop}: {exc}")

    dkm = imc.get_editor_property("default_key_mappings")
    mappings = dkm.get_editor_property("mappings")
    log(f"mapping count = {len(mappings)}")
    for i, m in enumerate(mappings):
        action = m.get_editor_property("action")
        aname = action.get_name() if action else None
        key = m.get_editor_property("key")
        if not aname or "Look" not in aname:
            continue
        log(f"[{i}] action={aname} key={key}")
        for mod in m.get_editor_property("modifiers"):
            dump_modifier(mod)

    log("done")


if __name__ == "__main__":
    main()
