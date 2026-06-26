"""Read SpawnAttachments graph and item data flow on swap."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_spawnatt_graph.log")
lines = []

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    if g.get_name() != "SpawnAttachments":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        lines.append(f"{node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')}")

# pickup attachment struct as pin string for construct object
pickup = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Pickup_Sniper.BP_Weapon_Pickup_Sniper"
)
cdo = unreal.get_default_object(pickup.generated_class())
lines.append("=== pickup attachment values ===")
for prop in (
    "Item Data AttachmentsSight",
    "Item Data AttachmentsLaser",
    "Item Data AttachmentsMuzzle",
    "Item Data Attachments Grip",
    "Item Data Ammo Count",
    "Item Data Max Ammo",
):
    val = cdo.get_editor_property(prop)
    lines.append(f"{prop}={val!r} name={val.name if hasattr(val,'name') else ''}")

# Build struct default string like construct pin uses
begin = None
bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if g.get_name() == "BeginSetup":
        begin = g
for node in unreal.BlueprintGraphEditor.get_graph_editor(begin).list_all_nodes():
    if node.get_name() == "K2Node_GenericCreateObject_1":
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if "Attachments" in pname:
                lines.append(f"throwable_attach_default={unreal.BlueprintGraphPinLibrary.get_pin_value(pin)!r}")

OUT.write_text("\n".join(lines))
