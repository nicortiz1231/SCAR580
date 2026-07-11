"""Check how BP_Laser is attached after spawn in AutomaticBase."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_laser_attach.log")
lines = []

bp = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase"
)
eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(eg)
for node in ed.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " ")
    if any(k in title for k in ("Attach", "SpawnActor BP Laser", "LaserRef", "Item_Mesh", "FinishSpawning")):
        lines.append(f"{node.get_name()} | {title}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            for cpin in pin.list_connected_pins():
                cn = cpin.get_owning_node()
                ct = str(cn.get_node_title()).replace("\n", " ")
                if any(k in ct for k in ("Attach", "Laser", "Mesh", "Spawn", "Socket", "Item")):
                    lines.append(f"  {pname} -> {cn.get_name()} | {ct}")

OUT.write_text("\n".join(lines))
