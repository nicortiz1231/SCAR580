"""Check SpawnAttachments override name and OpticSight default visibility."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_spawnatt_override.log")
lines = []

SNIPER = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper"
ITEM = "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base"

sniper_bp = unreal.load_asset(SNIPER)
item_bp = unreal.load_asset(ITEM)
cdo = unreal.get_default_object(sniper_bp.generated_class())

eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(sniper_bp))
for node in eg.list_all_nodes():
    cls = node.get_class().get_name()
    if cls not in ("K2Node_CustomEvent", "K2Node_Event"):
        continue
    title = str(node.get_node_title()).replace("\n", " | ")
    custom_name = ""
    try:
        custom_name = node.get_editor_property("custom_function_name")
    except Exception:
        pass
    lines.append(f"{node.get_name()} cls={cls} title={title} custom_function_name={custom_name!r}")

# item base SpawnAttachments custom event name
ieg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(item_bp))
for node in ieg.list_all_nodes():
    if node.get_class().get_name() != "K2Node_CustomEvent":
        continue
    title = str(node.get_node_title()).replace("\n", " | ")
    custom_name = node.get_editor_property("custom_function_name")
    lines.append(f"item {node.get_name()} title={title} name={custom_name!r}")

# OpticSight defaults on sniper CDO via component
try:
    optic = cdo.get_editor_property("OpticSight")
    lines.append(f"OpticSight component={optic}")
    if optic:
        for prop in ("static_mesh", "hidden_in_game", "visible", "bVisible", "bHiddenInGame"):
            try:
                lines.append(f"  {prop}={optic.get_editor_property(prop)!r}")
            except Exception as exc:
                lines.append(f"  {prop} ERR {exc}")
except Exception as exc:
    lines.append(f"optic ERR {exc}")

# check if character calls SpawnAttachments after equip - timing
char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
ceg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))
for node in ceg.list_all_nodes():
    if node.get_name() not in ("K2Node_CallFunction_140", "K2Node_CallFunction_141"):
        continue
    lines.append(f"char {node.get_name()} | {str(node.get_node_title()).replace(chr(10), ' | ')}")
    then = node.find_output_pin("then")
    if then:
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
            o = lp.get_owning_node()
            lines.append(f"  then -> {o.get_name()} | {str(o.get_node_title()).replace(chr(10), ' | ')}")

OUT.write_text("\n".join(lines))
