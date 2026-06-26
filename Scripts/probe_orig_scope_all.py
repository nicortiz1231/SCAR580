"""Find ALL scope/sight mesh application in original Bodycam project."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_orig_scope_all.log")
lines = []

SEARCH_PATHS = [
    "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Pickup",
]

for base in SEARCH_PATHS:
    bp = unreal.load_asset(f"{base}.{base.split('/')[-1]}")
    if not bp:
        lines.append(f"MISSING {base}")
        continue
    for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
        ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
        for node in ed.list_all_nodes():
            title = str(node.get_node_title()).replace("\n", " | ")
            if not any(k in title for k in ("SetStaticMesh", "SetSkeletalMesh", "ScopeSight", "OpticSight", "SM_4xScope", "ENUM_Sights", "SpawnAttachments")):
                continue
            if "SpareMag" in title:
                continue
            lines.append(f"[{bp.get_name()}/{g.get_name()}] {node.get_name()} | {title}")
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                if pn in ("execute", "then", "self", "NewMesh", "Selection"):
                    linked = [f"{lp.get_owning_node().get_name()}" for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
                    val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                    if linked or val:
                        lines.append(f"    {pn} -> {linked or val}")

# Akimbo Spawner full sight branch
item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    if g.get_name() != "Akimbo Spawner":
        continue
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append("\n=== Akimbo Spawner ENUM_Sights / mesh nodes ===")
    for node in ed.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if any(k in title for k in ("Switch", "Sight", "Scope", "SetStaticMesh", "SetSkeletalMesh", "AkimboSight", "OpticSight")):
            lines.append(f"  {node.get_name()} | {title}")

# Character equip -> SpawnAttachments backchain
char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
ced = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))
for node in ced.list_all_nodes():
    if node.get_name() not in ("K2Node_CallFunction_17", "K2Node_CallFunction_46", "K2Node_CallFunction_138"):
        continue
    lines.append(f"\n=== CHAR {node.get_name()} | {node.get_node_title()} ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        linked = [f"{lp.get_owning_node().get_name()}:{pn}" for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
        if linked:
            lines.append(f"  {pn} -> {linked}")

OUT.write_text("\n".join(lines))
