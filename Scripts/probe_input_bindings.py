"""Inspect IA_Look consume settings and legacy axis bindings on BP_FPCharacter."""

import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_input_bindings.log")


def log(msg: str) -> None:
    with open(LOG, "a") as f:
        f.write(msg + "\n")
    unreal.log(f"[probe_input_bindings] {msg}")


def main() -> None:
    open(LOG, "w").close()

    ia = unreal.load_asset("/Game/BodycamFPSKIT/Input/Actions/IA_Look.IA_Look")
    for prop in (
        "b_consume_input",
        "bConsumeInput",
        "trigger_events_that_consume_legacy_keys",
        "TriggerEventsThatConsumeLegacyKeys",
    ):
        try:
            log(f"IA_Look.{prop} = {ia.get_editor_property(prop)}")
        except Exception as exc:
            log(f"IA_Look.{prop}: {exc}")

    gen = unreal.load_asset(
        "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter"
    ).generated_class()

    for prop in (
        "input_axis_key_delegate_bindings",
        "InputAxisKeyDelegateBindings",
        "input_action_delegate_bindings",
        "InputActionDelegateBindings",
    ):
        try:
            bindings = gen.get_editor_property(prop)
            log(f"{prop} count={len(bindings) if bindings else 0}")
            if bindings:
                for b in bindings[:20]:
                    parts = []
                    for name in (
                        "input_axis_key",
                        "InputAxisKey",
                        "function_name_to_bind",
                        "FunctionNameToBind",
                        "input_key",
                        "InputKey",
                    ):
                        try:
                            val = b.get_editor_property(name)
                            if val is not None:
                                parts.append(f"{name}={val}")
                        except Exception:
                            pass
                    log(f"  binding: {' '.join(parts)}")
        except Exception as exc:
            log(f"{prop}: {exc}")

    log("done")


if __name__ == "__main__":
    main()
