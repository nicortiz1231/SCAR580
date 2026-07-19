"""Probe GetEquippedAnimset / EquippedGunSet / ENUM_Animset mapping."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_equipped_animset.log")
lines = []


def log(msg):
    lines.append(str(msg))
    print(msg)


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
gen = unreal.load_object(None, bp.get_path_name() + "_C")
cdo = unreal.get_default_object(gen)

for prop_name in ("EquippedGunSet", "EquippedWeapon", "Equipped", "IsWeapon", "IsAim"):
    prop = gen.find_property_by_name(prop_name) if hasattr(gen, "find_property_by_name") else None
    # UClass property walk
    found = None
    for p in gen.properties():
        if p.get_name() == prop_name:
            found = p
            break
    if not found:
        log(f"{prop_name}: NOT FOUND on class")
        continue
    try:
        val = cdo.get_editor_property(prop_name)
        log(f"{prop_name}: type={found.get_class().get_name()} value={val} ({type(val).__name__})")
    except Exception as exc:
        log(f"{prop_name}: read err {exc}")

# Enum assets
for enum_path in (
    "/Game/BodycamFPSKIT/Enums/ENUM_Animset.ENUM_Animset",
    "/Game/BodycamFPSKIT/Blueprints/ENUM_Animset.ENUM_Animset",
    "/Game/BodycamFPSKIT/Demo/Character/Mannequins/Animations/ENUM_Animset.ENUM_Animset",
):
    e = unreal.load_asset(enum_path)
    if e:
        log(f"ENUM loaded: {enum_path}")
        try:
            for i in range(e.get_editor_property("names").__len__() if False else 20):
                pass
        except Exception:
            pass
        try:
            # UserDefinedEnum
            display = e.get_editor_property("display_name_map")
            log(f"  display_name_map={display}")
        except Exception as exc:
            log(f"  display map err: {exc}")
        try:
            names = []
            for i in range(0, 16):
                try:
                    n = e.get_name_by_value(i)
                    names.append(f"{i}={n}")
                except Exception:
                    break
            log(f"  values: {names}")
        except Exception as exc:
            log(f"  values err: {exc}")

# Search asset registry for Animset enums
ar = unreal.AssetRegistryHelpers.get_asset_registry()
for asset in ar.get_assets_by_path("/Game/BodycamFPSKIT", recursive=True):
    name = str(asset.asset_name)
    if "Animset" in name or "GunSet" in name:
        log(f"asset: {asset.package_name}.{asset.asset_name} class={asset.asset_class_path}")

# Dump GetEquippedAnimset graph nodes
try:
    graphs = unreal.BlueprintEditorLibrary.get_all_graphs(bp) if hasattr(unreal, "BlueprintEditorLibrary") else []
except Exception:
    graphs = []

try:
    # Fallback: iterate ubergraph
    for g in bp.get_editor_property("function_graphs") if False else []:
        pass
except Exception:
    pass

# Use BlueprintEditorLibrary
try:
    all_graphs = []
    # UE5 API
    uber = bp.ubergraph_pages
    for g in uber:
        all_graphs.append(g)
    for g in bp.function_graphs:
        all_graphs.append(g)
    for g in all_graphs:
        gname = g.get_name()
        if "Equipped" not in gname and "Animset" not in gname and "Gun" not in gname:
            continue
        log(f"=== graph {gname} ===")
        for node in g.nodes:
            title = str(node.get_node_title(unreal.NodeTitleType.FULL_TITLE)).replace("\n", " | ")
            log(f"  {node.get_name()} | {node.get_class().get_name()} | {title}")
except Exception as exc:
    log(f"graph dump err: {exc}")

OUT.write_text("\n".join(lines) + "\n")
log(f"wrote {OUT}")
