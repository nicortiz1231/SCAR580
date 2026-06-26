"""Verify post-restore sniper state."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/verify_sniper_restore.log")
lines = []

sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
cdo = unreal.get_default_object(sniper.generated_class())
lines.append(f"AimDistance={cdo.get_editor_property('AimDistanceFromCamera')}")
lines.append(f"Optic={cdo.get_editor_property('OpticSightMesh').get_name()}")
lines.append(f"Scope={cdo.get_editor_property('ScopeSightMesh').get_name()}")

for gname in ("EventGraph", "UserConstructionScript"):
    g = next((g for g in unreal.BlueprintEditorLibrary.list_graphs(sniper) if g.get_name() == gname), None)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append(f"=== {gname} ({len(editor.list_all_nodes())} nodes) ===")
    for node in editor.list_all_nodes():
        lines.append(f"  {node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')}")

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
ied = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(item))
for node in ied.list_all_nodes():
    if "SpawnAttachments" in str(node.get_node_title()) and node.get_class().get_name() == "K2Node_CustomEvent":
        then = node.find_output_pin("then")
        linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then)] if then else []
        lines.append(f"Item SpawnAttachments then -> {linked or 'NONE'}")

OUT.write_text("\n".join(lines))
