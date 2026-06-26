import unreal
from pathlib import Path
OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_automatic_base.log")
lines = []
char_bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char_bp))
for class_path in (
    "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase_C",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/AutomaticBase/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase_C",
):
    for member in ("ScopeSightMesh", "OpticSight", "OpticSightMesh"):
        try:
            node = editor.add_get_member_variable_node(member, class_path)
            lines.append(f"OK {class_path} {member} -> {node.get_name() if node else None}")
            if node:
                editor.remove_nodes([node])
        except Exception as exc:
            lines.append(f"FAIL {class_path} {member}: {exc}")
item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
cdo = unreal.get_default_object(item.generated_class())
lines.append(f"item parent={cdo.get_class().get_super_class().get_name()}")
OUT.write_text("\n".join(lines))
