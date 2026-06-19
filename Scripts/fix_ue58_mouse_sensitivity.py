"""Apply UE 5.8 mouse look scale to match 5.7 DefaultInput.ini Mouse2D sensitivity (0.07)."""

import unreal
from pathlib import Path

IMC_PATH = "/Game/BodycamFPSKIT/Input/IMC_Player_Default"
MOUSE_SCALE = 0.07
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_ue58_mouse_sensitivity.log")


def log(msg: str) -> None:
    text = LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n"
    LOG_PATH.write_text(text)
    unreal.log(f"[fix_ue58_mouse_sensitivity] {msg}")


def has_scalar_modifier(modifiers) -> bool:
    for mod in modifiers:
        if mod and "Scalar" in mod.get_class().get_name():
            scalar = mod.get_editor_property("scalar")
            if abs(scalar.x - MOUSE_SCALE) < 1e-4 and abs(scalar.y - MOUSE_SCALE) < 1e-4:
                return True
    return False


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    imc = unreal.load_asset(f"{IMC_PATH}.IMC_Player_Default")
    if not imc:
        raise RuntimeError(f"Missing {IMC_PATH}")

    dkm = imc.get_editor_property("default_key_mappings")
    mappings = dkm.get_editor_property("mappings")
    updated = False

    for mapping in mappings:
        action = mapping.get_editor_property("action")
        if not action or action.get_name() != "IA_Look":
            continue
        key_name = mapping.get_editor_property("key").get_editor_property("key_name")
        if str(key_name) != "Mouse2D":
            continue

        modifiers = list(mapping.get_editor_property("modifiers"))
        if has_scalar_modifier(modifiers):
            log(f"IA_Look Mouse2D already has {MOUSE_SCALE} scalar modifier")
            continue

        scalar_mod = unreal.InputModifierScalar()
        scalar_mod.set_editor_property(
            "scalar", unreal.Vector(MOUSE_SCALE, MOUSE_SCALE, MOUSE_SCALE)
        )
        modifiers.insert(0, scalar_mod)
        mapping.set_editor_property("modifiers", modifiers)
        updated = True
        log(f"Added InputModifierScalar({MOUSE_SCALE}) to IA_Look Mouse2D mapping")

    if updated:
        unreal.EditorAssetLibrary.save_asset(IMC_PATH, only_if_is_dirty=False)
        log("Saved IMC_Player_Default")
    else:
        log("No IMC changes needed")

    log("done")


if __name__ == "__main__":
    main()
