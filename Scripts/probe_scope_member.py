"""Find which class exposes ScopeSightMesh for member get."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_scope_member.log")
lines = []

char_bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
)

for class_path in (
    "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base_C",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper_C",
):
    for member in ("ScopeSightMesh", "OpticSightMesh", "OpticSight"):
        try:
            node = editor.add_get_member_variable_node(member, class_path)
            lines.append(f"OK {class_path.split('/')[-1]} {member} -> {node.get_name() if node else None}")
            if node:
                editor.remove_nodes([node])
        except Exception as exc:
            lines.append(f"FAIL {class_path.split('/')[-1]} {member}: {exc}")

OUT.write_text("\n".join(lines))
