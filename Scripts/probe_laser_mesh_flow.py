"""Find all graph nodes connected to LaserMesh / LaserRef in weapon blueprints."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_laser_mesh_flow.log")
lines = []

ASSETS = [
    "/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base",
]

KEYWORDS = ("LaserMesh", "LaserRef", "AkimboLaserRef", "ToggleLaser", "ToggleFlashlight", "Material Reload", "AimReload")


def node_title(node):
    return str(node.get_node_title()).replace("\n", " ")


for base in ASSETS:
    name = base.split("/")[-1]
    bp = unreal.load_asset(f"{base}.{name}")
    lines.append(f"\n======== {name} ========")
    for graph in unreal.BlueprintEditorLibrary.list_graphs(bp):
        ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        hits = []
        for node in ed.list_all_nodes():
            title = node_title(node)
            if not any(k in title for k in KEYWORDS):
                continue
            hits.append(node)
        if not hits:
            continue
        lines.append(f"\n--- {graph.get_name()} ---")
        for node in hits:
            lines.append(f"  {node.get_name()} | {node_title(node)}")
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                for cpin in pin.list_connected_pins():
                    cnode = cpin.get_owning_node()
                    if not cnode:
                        continue
                    ct = node_title(cnode)
                    if any(k in ct for k in KEYWORDS + ("SetVisibility", "IsAim", "Reload", "Hidden", "Branch", "Switch")):
                        cpname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(cpin))
                        lines.append(
                            f"    {pname} -> {cnode.get_name()} | {ct} .{cpname}"
                        )

OUT.write_text("\n".join(lines))
