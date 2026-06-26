"""Probe sniper ADS clipping: camera near clip, OpticSight transform, AimDownSight."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sniper_ads_clip.log")
lines = []


def log(msg: str) -> None:
    lines.append(msg)
    unreal.log(msg)


char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
cdo = unreal.get_default_object(char.generated_class())
for comp_name in ("FirstPersonCamera", "Camera"):
    try:
        cam = cdo.get_editor_property(comp_name)
        if cam:
            for prop in ("field_of_view", "relative_location", "relative_rotation"):
                try:
                    log(f"char.{comp_name}.{prop}={cam.get_editor_property(prop)!r}")
                except Exception:
                    pass
            for prop in dir(cam):
                if "clip" in prop.lower() or "near" in prop.lower():
                    try:
                        log(f"char.{comp_name}.{prop}={cam.get_editor_property(prop)!r}")
                    except Exception:
                        pass
    except Exception as e:
        log(f"char.{comp_name} err={e}")

# BeginPlay near clip wiring
eg = unreal.BlueprintEditorLibrary.find_event_graph(char)
editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)
for node in editor.list_all_nodes():
    title = str(node.get_node_title())
    if "SetNearClipPlane" in title or "NearClip" in title:
        log(f"char BeginPlay graph: {node.get_name()} | {title.replace(chr(10), ' | ')}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            if val:
                log(f"  pin {pn}={val}")

sniper = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper"
)
scdo = unreal.get_default_object(sniper.generated_class())
log(f"sniper AimDistanceFromCamera={scdo.get_editor_property('AimDistanceFromCamera')}")

for comp_name in ("OpticSight", "WeaponMesh", "SkeletalMesh"):
    try:
        comp = scdo.get_editor_property(comp_name)
        if not comp:
            continue
        log(
            f"sniper.{comp_name} mesh={comp.get_editor_property('static_mesh') or comp.get_editor_property('skeletal_mesh')!r}"
        )
        log(f"  rel_loc={comp.get_editor_property('relative_location')!r}")
        log(f"  rel_rot={comp.get_editor_property('relative_rotation')!r}")
        log(f"  rel_scale={comp.get_editor_property('relative_scale3d')!r}")
    except Exception as e:
        log(f"sniper.{comp_name} err={e}")

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    if g.get_name() != "AimDownSight":
        continue
    ged = unreal.BlueprintGraphEditor.get_graph_editor(g)
    log(f"=== AimDownSight ({len(ged.list_all_nodes())} nodes) ===")
    for node in ged.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if any(
            k in title.lower()
            for k in ("aim", "distance", "camera", "offset", "clip", "wall", "loc", "scope", "fov")
        ):
            log(f"  {node.get_name()} | {title}")
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                if any(k in pn.lower() for k in ("aim", "distance", "offset", "loc", "clip", "fov")):
                    val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                    linked = [
                        lp.get_owning_node().get_name()
                        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)
                    ]
                    log(f"    {pn} val={val!r} linked={linked}")

OUT.write_text("\n".join(lines))
