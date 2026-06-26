"""Find sight visibility/mesh logic on character and item."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sight_visibility_flow.log")
lines = []

paths = (
    "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper",
)

for path in paths:
    bp = unreal.load_asset(path)
    lines.append(f"=== {path.split('/')[-1]} ===")
    for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
        editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
        for node in editor.list_all_nodes():
            title = str(node.get_node_title()).replace("\n", " | ")
            if not any(k in title for k in ("SetVisibility", "SetHiddenInGame", "SetStaticMesh", "Hide", "Show")):
                continue
            if "OpticSight" not in title and "ScopeSight" not in title:
                # include if self pin links to optic
                self_pin = node.find_input_pin("self") if hasattr(node, "find_input_pin") else None
                linked_optic = False
                if self_pin:
                    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(self_pin):
                        o = lp.get_owning_node()
                        ot = str(o.get_node_title())
                        if "OpticSight" in ot or "ScopeSight" in ot:
                            linked_optic = True
                if not linked_optic and "SetStaticMesh" not in title:
                    continue
            lines.append(f"[{g.get_name()}] {node.get_name()} | {title}")
            for pn in ("self", "bNewVisibility", "NewMesh", "NewHidden"):
                pin = node.find_input_pin(pn) if hasattr(node, "find_input_pin") else None
                if not pin:
                    continue
                val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                linked = []
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                    o = lp.get_owning_node()
                    linked.append(str(o.get_node_title()).replace("\n", " | "))
                if val or linked:
                    lines.append(f"  {pn}: val={val!r} linked={linked}")

OUT.write_text("\n".join(lines))
