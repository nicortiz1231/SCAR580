"""Find ToggleLaser / LaserMesh wiring around Reload and SpawnAttachments."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_laser_reload_chain.log")
lines = []

bp = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase"
)
eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(eg)

KEYWORDS = (
    "ToggleLaser", "ToggleFlashlight", "LaserMesh", "LaserRef", "Event Reload",
    "SpawnAttachments", "SetStaticMesh", "LaserActive", "Set with Notify",
)

for node in ed.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " ")
    if not any(k in title for k in KEYWORDS):
        continue
    lines.append(f"\n{node.get_name()} | {title}")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        for cpin in pin.list_connected_pins():
            cn = cpin.get_owning_node()
            ct = str(cn.get_node_title()).replace("\n", " ")
            lines.append(f"  {pname} <-> {cn.get_name()} | {ct}")

OUT.write_text("\n".join(lines))
