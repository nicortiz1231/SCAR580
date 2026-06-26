"""Probe AC_ProceduralAnimation aim timeline and ADS weapon offset."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_procedural_aim.log")
lines = []

ac = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Components/AC_ProceduralAnimation.AC_ProceduralAnimation")
cdo = unreal.get_default_object(ac.generated_class())
lines.append("=== AC_ProceduralAnimation CDO ===")
for prop in sorted(dir(cdo)):
    if prop.startswith("_"):
        continue
    lower = prop.lower()
    if not any(k in lower for k in ("aim", "ads", "sight", "loc", "offset", "distance", "clip", "pose", "weapon")):
        continue
    try:
        v = cdo.get_editor_property(prop)
        lines.append(f"  {prop}={v!r}")
    except Exception:
        pass

for g in unreal.BlueprintEditorLibrary.list_graphs(ac):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        cls = node.get_class().get_name()
        if any(k in title.lower() for k in ("aim", "timeline", "ads", "sight", "distance", "lerp", "alpha")):
            lines.append(f"[{g.get_name()}] {node.get_name()} | {cls} | {title}")
            if "MacroInstance" in cls or "Timeline" in cls:
                for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                    pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                    val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                    if val or pn in ("PlayRate", "NewTime", "Length"):
                        lines.append(f"    {pn}={val!r}")

# current sniper tuned values
sniper = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper"
)
scdo = unreal.get_default_object(sniper.generated_class())
lines.append(f"\n=== Current sniper ===")
lines.append(f"AimDistanceFromCamera={scdo.get_editor_property('AimDistanceFromCamera')}")
dt = scdo.get_editor_property("ProceduralValues")
wv = dt.get_editor_property("WeaponValues")
loc = wv.get_editor_property("BasePoseLoc")
lines.append(f"BasePoseLoc=({loc.x:.4f},{loc.y:.4f},{loc.z:.4f})")

OUT.write_text("\n".join(lines))
