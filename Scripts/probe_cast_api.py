"""Test BlueprintGraphEditor.cast API."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_cast_api.log")
lines = []

sniper_bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
char_bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
)

cast_fn = getattr(editor, "cast", None)
lines.append(f"cast={cast_fn}")
if cast_fn:
    try:
        node = cast_fn(sniper_bp.generated_class())
        lines.append(f"cast node={node} title={node.get_node_title() if node else None}")
        if node:
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                lines.append(f"  pin {pn}")
            editor.remove_nodes([node])
    except Exception as exc:
        lines.append(f"cast ERR {exc}")

# try add_get_member with class path
try:
    node2 = editor.add_get_member_variable_node("OpticSight", sniper_bp.generated_class())
    lines.append(f"member with class={node2}")
    if node2:
        editor.remove_nodes([node2])
except Exception as exc:
    lines.append(f"member class ERR {exc}")

OUT.write_text("\n".join(lines))
