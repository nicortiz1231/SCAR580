"""Probe sniper procedural/recoil values and camera near clip."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sniper_recoil.log")
lines = []

# sniper procedural data table
dt_path = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/DT_SniperAnimationValues"
dt = unreal.load_asset(dt_path)
lines.append(f"DT={dt} class={dt.get_class().get_name() if dt else None}")
if dt:
    for prop in sorted(dir(dt)):
        if prop.startswith("_"):
            continue
        try:
            val = dt.get_editor_property(prop)
            if val is not None and val != "" and val is not False:
                lines.append(f"  {prop}={val!r}")
        except Exception:
            pass

# compare rifle DT
for label, path in (
    ("sniper", "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/DT_SniperAnimationValues"),
    ("rifle", "/Game/BodycamFPSKIT/Blueprints/Interactables/AmericanRifle/DT_AmericanRifleAnimationValues"),
):
    asset = unreal.load_asset(path)
    if not asset:
        lines.append(f"MISSING {path}")
        continue
    lines.append(f"=== {label} ===")
    for prop in sorted(dir(asset)):
        if prop.startswith("_"):
            continue
        lower = prop.lower()
        if not any(k in lower for k in ("recoil", "ads", "weapon", "kick", "offset", "loc", "rot", "value")):
            continue
        try:
            val = asset.get_editor_property(prop)
            lines.append(f"  {prop}={val!r}")
        except Exception:
            pass

# character camera near clip
bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
for handle in sds.k2_gather_subobject_data_for_blueprint(bp):
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
    if not obj or "FirstPersonCamera" not in obj.get_name():
        continue
    lines.append(f"=== {obj.get_name()} ===")
    for prop in ("near_clip_plane", "field_of_view", "relative_location"):
        try:
            lines.append(f"  {prop}={obj.get_editor_property(prop)!r}")
        except Exception as exc:
            lines.append(f"  {prop} ERR {exc}")

# character Recoil function nodes
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if g.get_name() != "Recoil":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append(f"=== Recoil graph ({len(editor.list_all_nodes())} nodes) ===")
    for node in editor.list_all_nodes()[:25]:
        lines.append(f"  {node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')}")

OUT.write_text("\n".join(lines))
