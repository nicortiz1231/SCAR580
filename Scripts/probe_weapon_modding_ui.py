"""Probe Bodycam weapon modding UI wiring on BP_FPCharacter."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_weapon_modding_ui.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
cdo = unreal.get_default_object(bp.generated_class())

for prop in (
    "UI_Modding", "UI_ModdingRef", "UI_Hud", "UIcontrols", "controls",
    "SpawnedItem", "EquippedWeapon",
):
    try:
        val = cdo.get_editor_property(prop)
        lines.append(f"CDO {prop}={val!r}")
    except Exception as exc:
        lines.append(f"CDO {prop} ERR {exc}")

# widget class
for path in (
    "/Game/BodycamFPSKIT/Blueprints/Widgets/UI_WeaponModding",
    "/Game/BodycamFPSKIT/Input/Actions/IA_Modding",
):
    asset = unreal.load_asset(path)
    lines.append(f"ASSET {path} -> {asset}")

# all graphs / nodes related to modding
keywords = ("Modding", "WeaponModding", "UI_Modding", "CloseModding", "IA_Modding", "Inspect")
for graph in unreal.BlueprintEditorLibrary.list_graphs(bp):
    gname = graph.get_name()
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    hits = []
    for node in ed.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if any(k in title for k in keywords):
            hits.append(f"  {node.get_name()} | {title}")
        if any(k in node.get_name() for k in ("Modding", "WeaponModding")):
            hits.append(f"  {node.get_name()} | {title}")
    if hits:
        lines.append(f"\n=== graph {gname} ===")
        lines.extend(hits)

# function list
for graph in unreal.BlueprintEditorLibrary.list_graphs(bp):
    gname = graph.get_name()
    if any(k.lower() in gname.lower() for k in ("modding", "hud", "create")):
        lines.append(f"GRAPH {gname}")

# custom events
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(bp))
for node in eg.list_all_nodes():
    if node.get_class().get_name() == "K2Node_CustomEvent":
        title = str(node.get_node_title()).replace("\n", " | ")
        if any(k in title for k in keywords):
            lines.append(f"CUSTOM_EVENT {node.get_name()} | {title}")

# component check
subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
handles = subsystem.k2_gather_subobject_data_for_blueprint(bp)
lines.append("\n=== components ===")
for handle in handles:
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
    if obj:
        name = obj.get_name()
        cls = obj.get_class().get_name()
        if "SCAR" in cls or "Weapon" in cls or "Attachment" in cls:
            lines.append(f"  {name} | {cls}")

OUT.write_text("\n".join(lines))
