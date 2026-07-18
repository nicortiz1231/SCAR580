"""Verify ABP_Mirror / ABP_FP_ArmsProcedural exist and dump their variables + pawn weapon vars."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_mirror_assets.log")
lines = []


def log(msg):
    lines.append(str(msg))


KEYWORDS = ("gun", "weapon", "aim", "equip", "fire", "shoot", "ads", "pistol", "rifle", "anim", "mirror", "hand", "item")


def dump_class_props(klass, label):
    log(f"--- {label} properties (keyword filtered) ---")
    try:
        cdo = unreal.get_default_object(klass)
        for attr in dir(cdo):
            if any(k in attr.lower() for k in KEYWORDS):
                try:
                    val = cdo.get_editor_property(attr)
                    log(f"  {attr} = {val}")
                except Exception:
                    log(f"  {attr} (unreadable)")
    except Exception as exc:
        log(f"  err: {exc}")


# 1. What's in the mannequin Animations folder?
log("=== /Game/BodycamFPSKIT/Demo/Character/Mannequins/Animations ===")
for a in unreal.EditorAssetLibrary.list_assets("/Game/BodycamFPSKIT/Demo/Character/Mannequins/Animations", recursive=True):
    log(f"  {a}")

# 2. ABP_Mirror
mirror_class = unreal.load_object(None, "/Game/BodycamFPSKIT/Demo/Character/Mannequins/Animations/ABP_Mirror.ABP_Mirror_C")
log(f"=== ABP_Mirror_C loaded: {bool(mirror_class)} ===")
if mirror_class:
    dump_class_props(mirror_class, "ABP_Mirror")

# 3. ABP_FP_ArmsProcedural
arms_class = unreal.load_object(None, "/Game/BodycamFPSKIT/Character/ABP_FP_ArmsProcedural.ABP_FP_ArmsProcedural_C")
log(f"=== ABP_FP_ArmsProcedural_C loaded: {bool(arms_class)} ===")
if arms_class:
    dump_class_props(arms_class, "ABP_FP_ArmsProcedural")

# 4. Pawn weapon-related vars
pawn_class = unreal.load_object(None, "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter_C")
log(f"=== BP_FPCharacter_C loaded: {bool(pawn_class)} ===")
if pawn_class:
    dump_class_props(pawn_class, "BP_FPCharacter")

# 5. SKM_Camera arms mesh exists?
arms_mesh = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Camera/SKM_Camera.SKM_Camera")
log(f"=== SKM_Camera loaded: {bool(arms_mesh)} ===")

OUT.write_text("\n".join(lines))
print("probe complete")
