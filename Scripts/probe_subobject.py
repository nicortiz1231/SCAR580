import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_subobject.log")
lines = []

def p(msg):
    lines.append(str(msg))

BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter"
bp = unreal.load_asset(BP)

for cls_name in ("SubobjectDataSubsystem", "EditorActorSubsystem", "UnrealEditorSubsystem"):
    try:
        cls = getattr(unreal, cls_name)
        sub = unreal.get_editor_subsystem(cls)
        p(f"{cls_name}: {sub}")
        for fn in sorted(dir(sub)):
            if any(k in fn.lower() for k in ("component", "subobject", "blueprint", "gather")):
                p(f"  {fn}")
    except Exception as exc:
        p(f"{cls_name}: ERR {exc}")

try:
    handles = unreal.SubobjectDataBlueprintFunctionLibrary.gather_subobjects_data_for_blueprint(bp)
    p(f"gather count {len(handles)}")
    for handle in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        p(f"  {data.get_display_name()} | {data.get_object_class().get_name()}")
except Exception as exc:
    p(f"gather ERR {exc}")

OUT.write_text("\n".join(lines))
