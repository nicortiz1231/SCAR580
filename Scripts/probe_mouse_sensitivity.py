"""Dump mouse look sensitivity-related defaults from BP_FPCharacter and input settings."""

import unreal

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
LOG = "/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_mouse_sensitivity.log"


def log(msg: str) -> None:
    with open(LOG, "a") as f:
        f.write(msg + "\n")
    unreal.log(f"[probe_mouse_sensitivity] {msg}")


def dump_obj_props(obj, label: str, names: list[str]) -> None:
    log(f"--- {label} ---")
    for name in names:
        for candidate in (name, name.lower(), f"_{name.lower()}"):
            try:
                val = obj.get_editor_property(candidate)
                log(f"  {candidate} = {val}")
                break
            except Exception:
                pass


def main() -> None:
    open(LOG, "w").close()
    bp = unreal.load_asset(f"{BP_PATH}.BP_FPCharacter")
    gen = bp.generated_class()
    cdo = unreal.get_default_object(gen)
    log(f"BP class: {gen.get_name()}")

    for name in (
        "MouseSens",
        "InvertMouse",
        "BODYCAM",
        "LookSensitivity",
        "MouseSensitivity",
        "Sens",
    ):
        try:
            val = cdo.get_editor_property(name)
            log(f"CDO {name} = {val}")
        except Exception as exc:
            log(f"CDO {name}: {exc}")

    for comp_name in ("AC_FreeAim", "AC_BodycamCamera"):
        try:
            comp = unreal.BlueprintEditorLibrary.get_component_template(bp, comp_name)
        except Exception as exc:
            log(f"{comp_name} template: {exc}")
            continue
        if not comp:
            log(f"{comp_name}: missing")
            continue
        for name in (
            "StartSensitivity",
            "HorizontalMouse",
            "VerticalMouse",
            "MouseSens",
            "Sensitivity",
        ):
            try:
                val = comp.get_editor_property(name)
                log(f"{comp_name}.{name} = {val}")
            except Exception:
                pass

    settings = unreal.get_default_object(unreal.InputSettings)
    for axis in settings.get_editor_property("axis_config"):
        key = str(axis.get_editor_property("axis_key_name"))
        if "Mouse" in key:
            props = axis.get_editor_property("axis_properties")
            log(
                f"Input axis {key}: sensitivity={props.get_editor_property('sensitivity')} "
                f"deadzone={props.get_editor_property('dead_zone')} exponent={props.get_editor_property('exponent')}"
            )

    log("done")


if __name__ == "__main__":
    main()
