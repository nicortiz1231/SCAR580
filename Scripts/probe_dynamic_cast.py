"""Try creating DynamicCast node in character graph."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_dynamic_cast.log")
lines = []

char_bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
sniper_bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
)

for method in ("add_dynamic_cast_node", "add_cast_node", "add_node"):
    fn = getattr(editor, method, None)
    lines.append(f"{method}={fn}")

try:
    cast_class = unreal.load_class(None, "/Script/BlueprintGraph.K2Node_DynamicCast")
    lines.append(f"cast_class={cast_class}")
    if cast_class:
        node = editor.add_node(cast_class)
        lines.append(f"add_node cast={node}")
        if node:
            try:
                node.set_editor_property("target_type", sniper_bp.generated_class())
                lines.append("set target_type ok")
            except Exception as exc:
                lines.append(f"set target_type ERR {exc}")
            editor.remove_nodes([node])
except Exception as exc:
    lines.append(f"add_node ERR {exc}")

OUT.write_text("\n".join(lines))
