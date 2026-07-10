import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_mirror_anim.log")
lines = []

def log(msg):
    lines.append(str(msg))

mirror_class = unreal.load_class(None, "/Game/BodycamFPSKIT/Demo/Character/Mannequins/Animations/ABP_Mirror.ABP_Mirror_C")
fp_class = unreal.load_class(None, "/Game/BodycamFPSKIT/Character/ABP_FP_ArmsProcedural.ABP_FP_ArmsProcedural_C")

for label, cls in (("Mirror", mirror_class), ("FPArms", fp_class)):
    if not cls:
        log(f"{label}: class missing")
        continue
    cdo = unreal.get_default_object(cls)
    log(f"=== {label} {cls.get_name()} ===")
    for prop in dir(cdo):
        if prop.startswith("_"):
            continue
        try:
            val = cdo.get_editor_property(prop)
            if val is not None and str(val) != "None":
                log(f"  {prop} = {val}")
        except Exception:
            pass

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for name in ("CharacterMesh", "CharacterMesh0"):
    comp = unreal.BlueprintEditorLibrary.get_component_template(bp, name)
    if not comp:
        log(f"TEMPLATE {name}: missing")
        continue
    mesh = comp.get_skeletal_mesh_asset()
    anim = comp.get_editor_property("anim_class")
    parent = comp.get_editor_property("attach_parent_name") if hasattr(comp, "get_editor_property") else None
    log(f"TEMPLATE {name}: mesh={mesh.get_path_name() if mesh else None} anim={anim.get_name() if anim else None}")

OUT.write_text("\n".join(lines))
unreal.log(f"Wrote {OUT}")
