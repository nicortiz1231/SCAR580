"""Tune UE 5.8 mouse look sensitivity on IMC_Player (runtime mapping context).

Adjust MOUSE_SCALE in small steps (e.g. 0.005) until feel matches original SCAR.
Original DefaultInput.ini uses 0.07; UE 5.8 needs this baked on IMC_Player because
Mouse2D no longer picks up axis config reliably, and legacy MouseX/Y can stack on top.
"""

import unreal
from pathlib import Path

IMC_PLAYER = "/Game/BodycamFPSKIT/Input/IMC_Player"
IA_LOOK = "/Game/BodycamFPSKIT/Input/Actions/IA_Look"
# Tuned between "way too fast" (unscaled) and "a bit slow" (0.07 + legacy block).
MOUSE_SCALE = 0.135
ENGINE_INI = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Config/DefaultEngine.ini")
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_ue58_mouse_sensitivity.log")


def log(msg: str) -> None:
    text = LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n"
    LOG_PATH.write_text(text)
    unreal.log(f"[fix_ue58_mouse_sensitivity] {msg}")


def remove_global_axis_cvar() -> None:
    text = ENGINE_INI.read_text()
    cleaned = text.replace("input.GlobalAxisConfigMode=1\n", "")
    if cleaned != text:
        ENGINE_INI.write_text(cleaned)
        log("Removed input.GlobalAxisConfigMode=1")


def get_scalar(mod) -> float | None:
    if mod and "Scalar" in mod.get_class().get_name():
        return float(mod.get_editor_property("scalar").x)
    return None


def make_scalar(outer, scale: float):
    mod = unreal.new_object(unreal.InputModifierScalar, outer=outer)
    mod.set_editor_property("scalar", unreal.Vector(scale, scale, scale))
    return mod


def apply_imc_scale() -> None:
    imc = unreal.load_asset(f"{IMC_PLAYER}.IMC_Player")
    if not imc:
        raise RuntimeError(f"Missing {IMC_PLAYER}")

    dkm = imc.get_editor_property("default_key_mappings")
    mappings = list(dkm.get_editor_property("mappings"))
    changed = False

    for index, mapping in enumerate(mappings):
        action = mapping.get_editor_property("action")
        if not action or action.get_name() != "IA_Look":
            continue
        if str(mapping.get_editor_property("key").get_editor_property("key_name")) != "Mouse2D":
            continue

        modifiers = [m for m in mapping.get_editor_property("modifiers") if get_scalar(m) is None]
        modifiers.insert(0, make_scalar(imc, MOUSE_SCALE))
        mapping.set_editor_property("modifiers", modifiers)
        mappings[index] = mapping
        changed = True
        log(f"IMC_Player IA_Look Mouse2D scale = {MOUSE_SCALE}")

    if changed:
        dkm.set_editor_property("mappings", mappings)
        imc.set_editor_property("default_key_mappings", dkm)
        unreal.EditorAssetLibrary.save_asset(IMC_PLAYER, only_if_is_dirty=False)
        log("Saved IMC_Player")


def block_duplicate_legacy_look() -> None:
    ia = unreal.load_asset(f"{IA_LOOK}.IA_Look")
    if not ia:
        raise RuntimeError(f"Missing {IA_LOOK}")

    changed = False
    if not ia.get_editor_property("bConsumesActionAndAxisMappings"):
        ia.set_editor_property("bConsumesActionAndAxisMappings", True)
        changed = True

    consume_mask = (
        int(unreal.TriggerEvent.TRIGGERED.value)
        | int(unreal.TriggerEvent.ONGOING.value)
    )
    if int(ia.get_editor_property("TriggerEventsThatConsumeLegacyKeys")) != consume_mask:
        ia.set_editor_property("TriggerEventsThatConsumeLegacyKeys", consume_mask)
        changed = True

    if changed:
        unreal.EditorAssetLibrary.save_asset(IA_LOOK, only_if_is_dirty=False)
        log("IA_Look now blocks duplicate legacy MouseX/Y look axes")


def verify() -> None:
    imc = unreal.load_asset(f"{IMC_PLAYER}.IMC_Player")
    dkm = imc.get_editor_property("default_key_mappings")
    for mapping in dkm.get_editor_property("mappings"):
        action = mapping.get_editor_property("action")
        if not action or action.get_name() != "IA_Look":
            continue
        if str(mapping.get_editor_property("key").get_editor_property("key_name")) != "Mouse2D":
            continue
        scalars = [get_scalar(m) for m in mapping.get_editor_property("modifiers") if get_scalar(m) is not None]
        log(f"VERIFY IMC_Player Mouse2D scalars={scalars}")


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    remove_global_axis_cvar()
    apply_imc_scale()
    block_duplicate_legacy_look()
    verify()
    log(f"Current MOUSE_SCALE={MOUSE_SCALE}. Nudge this constant in Scripts/fix_ue58_mouse_sensitivity.py if needed.")
    log("done")


if __name__ == "__main__":
    main()
