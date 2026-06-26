"""Same probe against pristine BODYCAMFPSKIT project."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_bodycam_original_state.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
cdo = unreal.get_default_object(bp.generated_class())
lines.append("=== ORIGINAL sniper CDO ===")
for prop in ("AimDistanceFromCamera", "ScopeSightMesh", "OpticSightMesh", "ProceduralValues"):
    v = cdo.get_editor_property(prop)
    lines.append(f"  {prop}={v.get_path_name() if hasattr(v,'get_path_name') else v}")

for gname in ("EventGraph", "UserConstructionScript"):
    g = next((g for g in unreal.BlueprintEditorLibrary.list_graphs(bp) if g.get_name() == gname), None)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append(f"=== ORIGINAL {gname} ===")
    for node in ed.list_all_nodes():
        lines.append(f"  {node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')}")

char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for g in unreal.BlueprintEditorLibrary.list_graphs(char):
    if g.get_name() != "BeginSetup":
        continue
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in ed.list_all_nodes():
        if node.get_name() != "K2Node_GenericCreateObject_2":
            continue
        lines.append("=== ORIGINAL HandsSlot ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            if val and "ItemData" in pn:
                lines.append(f"  {pn}={val}")

OUT.write_text("\n".join(lines))
