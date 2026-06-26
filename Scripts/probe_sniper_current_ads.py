"""Current sniper ADS distance + pose values."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sniper_current_ads.log")
lines = []

sniper = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper"
)
cdo = unreal.get_default_object(sniper.generated_class())
lines.append(f"AimDistanceFromCamera={cdo.get_editor_property('AimDistanceFromCamera')}")
lines.append(f"ChangeSightSpeed={cdo.get_editor_property('ChangeSightSpeed')}")

dt_path = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/DT_SniperAnimationValues"
dt = unreal.load_asset(f"{dt_path}.DT_SniperAnimationValues")
if dt:
    wv = dt.get_editor_property("WeaponValues")
    loc = wv.get_editor_property("BasePoseLoc")
    rot = wv.get_editor_property("BasePoseRot")
    lines.append(f"DT BasePoseLoc=({loc.x:.4f},{loc.y:.4f},{loc.z:.4f})")
    lines.append(f"DT BasePoseRot=(r{rot.roll:.2f},p{rot.pitch:.2f},y{rot.yaw:.2f})")
    for name in ("AimPoseLoc", "AimPoseRot", "SprintPoseLoc", "IdlePoseLoc"):
        try:
            v = wv.get_editor_property(name)
            if hasattr(v, "x"):
                lines.append(f"  {name}=({v.x:.4f},{v.y:.4f},{v.z:.4f})")
        except Exception:
            pass

# char near clip wiring
char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))
for node in eg.list_all_nodes():
    if "ExecuteConsoleCommand" not in str(node.get_node_title()):
        continue
    pin = node.find_input_pin("Command")
    if pin:
        val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
        if val and "NearClip" in val:
            lines.append(f"NearClip cmd: {val}")

OUT.write_text("\n".join(lines))
