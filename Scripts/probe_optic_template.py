"""Probe item UCS OpticSight logic and get_component_template for sniper."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_optic_template.log")
lines = []

SNIPER = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper"
ITEM = "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base"

sniper_bp = unreal.load_asset(SNIPER)
item_bp = unreal.load_asset(ITEM)

for name in ("OpticSight", "OpticSight_GEN_VARIABLE"):
    try:
        comp = unreal.BlueprintEditorLibrary.get_component_template(sniper_bp, name)
        lines.append(f"sniper get_component_template({name})={comp}")
        if comp:
            sm = comp.get_editor_property("static_mesh")
            lines.append(f"  mesh={sm.get_name() if sm else None}")
    except Exception as exc:
        lines.append(f"sniper {name} ERR {exc}")

# item UCS full chain around OpticSight
for g in unreal.BlueprintEditorLibrary.list_graphs(item_bp):
    if g.get_name() != "UserConstructionScript":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append("=== Item UCS nodes ===")
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        lines.append(f"  {node.get_name()} | {title}")

OUT.write_text("\n".join(lines))
