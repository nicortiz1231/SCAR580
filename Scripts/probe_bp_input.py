"""Inspect BP_FPCharacter mapping context and IA_Look input bindings."""

import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_bp_input.log")


def log(msg: str) -> None:
    with open(LOG, "a") as f:
        f.write(msg + "\n")
    unreal.log(f"[probe_bp_input] {msg}")


def try_props(obj, label, names):
    for name in names:
        try:
            val = obj.get_editor_property(name)
            if val is not None and val != "" and val != 0:
                if hasattr(val, "get_path_name"):
                    log(f"{label}.{name} = {val.get_path_name()}")
                else:
                    log(f"{label}.{name} = {val}")
        except Exception:
            pass


def main() -> None:
    open(LOG, "w").close()
    bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
    cdo = unreal.get_default_object(bp.generated_class())

    for name in dir(cdo):
        lower = name.lower()
        if any(k in lower for k in ("mapping", "input", "mouse", "sens", "context", "imc")):
            try:
                val = cdo.get_editor_property(name)
                if val is not None and val != "" and val != 0 and val is not False:
                    if hasattr(val, "get_path_name"):
                        log(f"CDO.{name} = {val.get_path_name()}")
                    else:
                        log(f"CDO.{name} = {val}")
            except Exception:
                pass

    try_props(
        cdo,
        "CDO",
        [
            "MappingContext",
            "DefaultMappingContext",
            "InputMappingContext",
            "IMC",
            "MouseSens",
            "InvertMouse",
        ],
    )

    # Blueprint default subobjects / component templates
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    for handle in sds.k2_gather_subobject_data_for_blueprint(bp):
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
        if not obj:
            continue
        if "FreeAim" in obj.get_name():
            for prop in (
                "StartSensitivity",
                "Horizontal Mouse",
                "Vertical Mouse",
                "Start Sensitivity",
            ):
                try:
                    log(f"{obj.get_name()}.{prop} = {obj.get_editor_property(prop)}")
                except Exception as exc:
                    log(f"{obj.get_name()}.{prop}: {exc}")

    # Enhanced input action bindings on generated class
    gen = bp.generated_class()
    for prop in ("input_action_delegate_bindings", "input_action_value_bindings"):
        try:
            bindings = gen.get_editor_property(prop)
            log(f"{prop} count={len(bindings) if bindings else 0}")
        except Exception as exc:
            log(f"{prop}: {exc}")

    log("done")


if __name__ == "__main__":
    main()
