"""Probe equip/swap sound nodes on weapon BPs."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_weapon_swap_sfx.log")
WEAPONS = (
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/AmericanRifle/BP_Weapon_AmericanRifle",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base",
)

SOUND = ("PlaySound", "SpawnSound")


def title(node) -> str:
    return str(node.get_node_title()).replace("\n", " | ")


lines = []
for path in WEAPONS:
    bp = unreal.load_asset(f"{path}.{path.split('/')[-1]}")
    if not bp:
        lines.append(f"MISSING {path}")
        continue
    for graph in unreal.BlueprintEditorLibrary.list_graphs(bp):
        editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        for node in editor.list_all_nodes():
            t = title(node)
            if any(s in t for s in SOUND):
                lines.append(f"{path} [{graph.get_name()}] {node.get_name()} | {t}")

OUT.write_text("\n".join(lines) if lines else "none\n")
