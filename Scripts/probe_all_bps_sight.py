"""Search all BP graphs for optic sight mesh assignment."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_all_bps_sight.log")
lines = []

paths = [
    "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/AmericanRifle/BP_Weapon_AmericanRifle.BP_Weapon_AmericanRifle",
]

for path in paths:
    bp = unreal.load_asset(path)
    if not bp:
        continue
    label = path.split("/")[-1]
    for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
        editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
        for node in editor.list_all_nodes():
            title = str(node.get_node_title()).replace("\n", " | ")
            if "SetStaticMesh" not in title:
                continue
            lines.append(f"[{label}/{g.get_name()}] {node.get_name()} | {title}")
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                if pn in ("self", "NewMesh"):
                    linked = []
                    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                        linked.append(str(lp.get_owning_node().get_node_title()).replace("\n"," | "))
                    try:
                        val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                        if val:
                            linked.append(val)
                    except Exception:
                        pass
                    lines.append(f"  {pn} -> {linked}")

OUT.write_text("\n".join(lines))
