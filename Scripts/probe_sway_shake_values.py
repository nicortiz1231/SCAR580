"""Dump current sway/shake tuning values relevant to AR arm jitter."""
import unreal
from pathlib import Path

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sway_shake_values.log")

INTERESTING_SUBSTRINGS = (
    "sway", "shake", "amplitude", "spring", "damp", "stiff", "recoil",
    "smooth", "lag", "interp", "threshold", "deadzone", "sensitiv",
)


def log(msg: str) -> None:
    line = str(msg)
    with LOG_PATH.open("a") as f:
        f.write(line + "\n")
    unreal.log(f"[probe_sway] {line}")


if LOG_PATH.exists():
    LOG_PATH.unlink()

bp = unreal.load_asset(BP_ASSET)
if not bp:
    raise RuntimeError(f"Missing {BP_ASSET}")

cdo = unreal.get_default_object(bp.generated_class())
comps = cdo.get_components_by_class(unreal.ActorComponent.static_class())
log(f"Found {len(comps)} components on BP_FPCharacter CDO")
for c in comps:
    log(f"  COMPONENT: {c.get_name()} ({c.get_class().get_name()})")

targets = [c for c in comps if any(n in c.get_name() for n in ("ProceduralAnimation", "BodycamCamera", "FreeAim", "RecoilClimb", "ProceduralRecoil"))]

if not targets:
    log("No name match; falling back to subobject data subsystem scan")
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    for handle in sds.k2_gather_subobject_data_for_blueprint(bp):
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
        if not obj:
            continue
        log(f"  SUBOBJ: {obj.get_name()} ({obj.get_class().get_name()})")
        if any(n in obj.get_name() for n in ("ProceduralAnimation", "BodycamCamera", "FreeAim", "RecoilClimb", "ProceduralRecoil")):
            targets.append(obj)

for comp in targets:
    log(f"\n=== {comp.get_name()} ({comp.get_class().get_name()}) ===")
    try:
        props = comp.get_class().get_editor_property("class_default_object")
    except Exception:
        props = None
    # Enumerate all UPROPERTY fields via get_editor_property using the UClass's property iterator.
    ustruct = comp.get_class()
    try:
        field_names = [str(p) for p in dir(comp)]
    except Exception:
        field_names = []

    # Fallback: use unreal's reflection to list properties directly.
    try:
        for prop in unreal.SystemLibrary.get_class_default_object(ustruct).get_editor_property.__self__.__class__.__dict__:
            pass
    except Exception:
        pass

    dir_names = [d for d in dir(comp) if not d.startswith("_")]
    matched = [d for d in dir_names if any(s in d.lower() for s in INTERESTING_SUBSTRINGS)]
    log(f"  dir() total={len(dir_names)} matched={len(matched)}")
    for pname in matched:
        try:
            val = getattr(comp, pname)
            val = val() if callable(val) else val
        except Exception as exc:
            val = f"ERR {exc}"
        log(f"  {pname} = {val}")

log("\nDONE")
