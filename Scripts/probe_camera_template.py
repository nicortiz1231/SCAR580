"""Find CameraFPS component template on BP_FPCharacter."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_camera_template.log")
lines = []


def p(msg):
    lines.append(str(msg))
    unreal.log(msg)


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
p(f"bp type={type(bp)} class={bp.get_class().get_name()}")

for attr in (
    "simple_construction_script",
    "SimpleConstructionScript",
    "ubergraph_pages",
    "function_graphs",
):
    try:
        val = bp.get_editor_property(attr)
        p(f"{attr}={val}")
    except Exception as exc:
        p(f"{attr}=ERR {exc}")

# Try blueprint generated class
gen = bp.generated_class()
p(f"generated={gen.get_name()}")

# Editor-only APIs
for api in (
    "get_editor_property",
):
    pass

try:
    lib = unreal.BlueprintEditorLibrary
    for fn in sorted(dir(lib)):
        if "component" in fn.lower() or "template" in fn.lower() or "scs" in fn.lower():
            p(f"BlueprintEditorLibrary.{fn}")
except Exception as exc:
    p(f"lib err {exc}")

# SubobjectDataSubsystem
try:
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    p(f"SubobjectDataSubsystem={sub}")
except Exception as exc:
    p(f"SubobjectDataSubsystem ERR {exc}")

# Asset editor
try:
    tools = unreal.AssetEditorSubsystem()
    p(f"AssetEditorSubsystem ok")
except Exception as exc:
    p(f"AssetEditorSubsystem ERR {exc}")

LOG.write_text("\n".join(lines))
