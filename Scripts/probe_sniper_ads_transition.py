"""Dump all sniper procedural anim + ADS transition fields."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sniper_ads_transition.log")
lines = []

sniper = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper"
)
cdo = unreal.get_default_object(sniper.generated_class())
lines.append("=== Sniper CDO ===")
for prop in sorted(dir(cdo)):
    if prop.startswith("_"):
        continue
    lower = prop.lower()
    if not any(k in lower for k in ("aim", "sight", "ads", "scope", "procedural", "change", "distance")):
        continue
    try:
        v = cdo.get_editor_property(prop)
        lines.append(f"  {prop}={v.get_path_name() if hasattr(v, 'get_path_name') else v!r}")
    except Exception:
        pass

dt = cdo.get_editor_property("ProceduralValues")
lines.append(f"\n=== DT {dt.get_name()} all props ===")
for prop in sorted(dir(dt)):
    if prop.startswith("_"):
        continue
    try:
        v = dt.get_editor_property(prop)
        if hasattr(v, "x"):
            lines.append(f"  {prop}=({v.x:.4f},{v.y:.4f},{v.z:.4f})")
        elif hasattr(v, "pitch"):
            lines.append(f"  {prop}=(p{v.pitch:.2f},y{v.yaw:.2f},r{v.roll:.2f})")
        else:
            lines.append(f"  {prop}={v!r}")
    except Exception as exc:
        lines.append(f"  {prop} ERR {exc}")

for block_name in ("WeaponValues", "RecoilValues"):
    try:
        block = dt.get_editor_property(block_name)
        lines.append(f"\n=== {block_name} all props ===")
        for prop in sorted(dir(block)):
            if prop.startswith("_"):
                continue
            try:
                v = block.get_editor_property(prop)
                if hasattr(v, "x"):
                    lines.append(f"  {prop}=({v.x:.4f},{v.y:.4f},{v.z:.4f})")
                elif hasattr(v, "pitch"):
                    lines.append(f"  {prop}=(p{v.pitch:.2f},y{v.yaw:.2f},r{v.roll:.2f})")
                else:
                    lines.append(f"  {prop}={v!r}")
            except Exception:
                pass
    except Exception as exc:
        lines.append(f"{block_name} ERR {exc}")

# rifle compare
rifle = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/AmericanRifle/BP_Weapon_AmericanRifle.BP_Weapon_AmericanRifle"
)
rcdo = unreal.get_default_object(rifle.generated_class())
lines.append("\n=== Rifle compare ===")
lines.append(f"  AimDistanceFromCamera={rcdo.get_editor_property('AimDistanceFromCamera')}")
lines.append(f"  ChangeSightSpeed={rcdo.get_editor_property('ChangeSightSpeed')}")
rpv = rcdo.get_editor_property("ProceduralValues")
rwv = rpv.get_editor_property("WeaponValues")
loc = rwv.get_editor_property("BasePoseLoc")
lines.append(f"  BasePoseLoc=({loc.x:.4f},{loc.y:.4f},{loc.z:.4f})")

# item AimDownSight graph key nodes
item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    if g.get_name() != "AimDownSight":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append(f"\n=== AimDownSight ({len(editor.list_all_nodes())} nodes) ===")
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if any(k in title.lower() for k in ("aim", "distance", "lerp", "alpha", "timeline", "interp", "camera", "loc", "offset", "procedural")):
            lines.append(f"  {node.get_name()} | {title}")

OUT.write_text("\n".join(lines))
