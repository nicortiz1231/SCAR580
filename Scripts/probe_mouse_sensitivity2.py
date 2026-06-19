"""Compare AC_FreeAim StartSensitivity and IA_Look between projects."""

import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_mouse_sensitivity.log")


def log(msg: str) -> None:
    with open(LOG, "a") as f:
        f.write(msg + "\n")
    unreal.log(f"[probe_mouse_sensitivity2] {msg}")


def main() -> None:
    with open(LOG, "a") as f:
        f.write("\n--- probe2 ---\n")

    bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    for handle in sds.k2_gather_subobject_data_for_blueprint(bp):
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
        if not obj:
            continue
        name = obj.get_name()
        if "FreeAim" not in name:
            continue
        for prop in (
            "StartSensitivity",
            "HorizontalMouse",
            "VerticalMouse",
            "Start Sensitivity",
            "Horizontal Mouse",
            "Vertical Mouse",
        ):
            try:
                log(f"{name}.{prop} = {obj.get_editor_property(prop)}")
            except Exception as exc:
                log(f"{name}.{prop}: {exc}")

    ia = unreal.load_asset("/Game/BodycamFPSKIT/Input/Actions/IA_Look.IA_Look")
    if ia:
        for prop in (
            "value_type",
            "modifiers",
            "accumulation_behavior",
            "trigger_when_paused",
        ):
            try:
                log(f"IA_Look.{prop} = {ia.get_editor_property(prop)}")
            except Exception as exc:
                log(f"IA_Look.{prop}: {exc}")
        try:
            mods = ia.get_editor_property("modifiers")
            log(f"IA_Look modifier count = {len(mods)}")
            for i, mod in enumerate(mods):
                log(f"  mod[{i}] class={mod.get_class().get_name()} name={mod.get_name()}")
                for p in dir(mod):
                    if "scale" in p.lower() or "sens" in p.lower():
                        try:
                            log(f"    {p}={mod.get_editor_property(p)}")
                        except Exception:
                            pass
        except Exception as exc:
            log(f"IA_Look modifiers err: {exc}")

    for path in (
        "/Game/BodycamFPSKIT/Input/IMC_Player.IMC_Player",
        "/Game/BodycamFPSKIT/Input/IMC_Player_Default.IMC_Player_Default",
    ):
        imc = unreal.load_asset(path)
        if not imc:
            log(f"missing {path}")
            continue
        mappings = imc.get_editor_property("mappings")
        log(f"{path} mappings={len(mappings)}")
        for m in mappings:
            action = m.get_editor_property("action")
            aname = action.get_name() if action else None
            if aname and "Look" in aname:
                log(
                    f"  Look mapping key={m.get_editor_property('key')} "
                    f"triggers={m.get_editor_property('triggers')} "
                    f"modifiers={m.get_editor_property('modifiers')}"
                )

    log("probe2 done")


if __name__ == "__main__":
    main()
