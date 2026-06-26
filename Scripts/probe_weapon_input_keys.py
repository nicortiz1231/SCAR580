"""Probe weapon slot input bindings and swipe wiring state."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_weapon_input_keys.log")
lines = []


def log(msg: str) -> None:
    lines.append(msg)
    unreal.log(msg)


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)

for node in editor.list_all_nodes():
    cls = node.get_class().get_name()
    title = str(node.get_node_title()).replace("\n", " | ")
    if cls == "K2Node_EnhancedInputAction" and ("Primary" in title or "Secondary" in title or "Slot" in title):
        log(f"EIA {node.get_name()} | {title}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) != unreal.EdGraphPinDirection.EGPD_OUTPUT:
                continue
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if pname == "Triggered":
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                    owner = lp.get_owning_node()
                    log(f"  Triggered -> {owner.get_name()} | {str(owner.get_node_title()).replace(chr(10), ' | ')}")

    if "Weapon Swipe" in title or (cls == "EdGraphNode_Comment" and "Weapon Swipe" in str(node.get_editor_property("node_comment") if hasattr(node, 'get_editor_property') else "")):
        try:
            log(f"COMMENT {node.get_editor_property('node_comment')}")
        except Exception:
            pass

for asset_path in (
    "/Game/BodycamFPSKIT/Input/IMC_Default.IMC_Default",
    "/Game/BodycamFPSKIT/Input/IMC_Bodycam.IMC_Bodycam",
    "/Game/SCAR580/Input/IMC_Mobile.IMC_Mobile",
):
    imc = unreal.load_asset(asset_path)
    if not imc:
        log(f"MISSING {asset_path}")
        continue
    log(f"=== {asset_path} ===")
    try:
        mappings = imc.get_editor_property("mappings")
        for m in mappings:
            action = m.get_editor_property("action")
            aname = action.get_name() if action else "?"
            triggers = [t.get_class().get_name() for t in m.get_editor_property("triggers")]
            mods = m.get_editor_property("modifiers")
            keys = []
            for mod in mods:
                if mod and "InputModifier" in mod.get_class().get_name():
                    pass
            # get key from mapping
            try:
                key = m.get_editor_property("key")
                keys.append(str(key))
            except Exception:
                pass
            log(f"  {aname} key={keys} triggers={triggers}")
    except Exception as exc:
        log(f"  ERR {exc}")

# find IA assets
for path in unreal.EditorAssetLibrary.list_assets("/Game", recursive=True, include_folder=False):
    if "IA_" in path and ("Primary" in path or "Secondary" in path or "Slot" in path):
        log(f"IA asset: {path}")

OUT.write_text("\n".join(lines))
