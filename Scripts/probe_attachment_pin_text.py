"""Find correct attachment struct pin text from pickup CDO."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_attachment_pin_text.log")
lines = []

pickup = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Pickup_Sniper.BP_Weapon_Pickup_Sniper")
cdo = unreal.get_default_object(pickup.generated_class())

for name in (
    "Item Data AttachmentsSight", "Item Data AttachmentsLaser",
    "Item Data AttachmentsMuzzle", "Item Data Attachments Grip",
):
    val = cdo.get_editor_property(name)
    lines.append(f"{name}={val!r} type={type(val).__name__}")

# try build struct string
try:
    sight = cdo.get_editor_property("Item Data AttachmentsSight")
    laser = cdo.get_editor_property("Item Data AttachmentsLaser")
    muzzle = cdo.get_editor_property("Item Data AttachmentsMuzzle")
    grip = cdo.get_editor_property("Item Data Attachments Grip")
    lines.append(f"\nEnum indices: sight={int(sight)} laser={int(laser)} muzzle={int(muzzle)} grip={int(grip)}")
    for label, val, enum_name in (
        ("Sight", sight, "NUM_Sights"),
        ("Laser", laser, "NUM_Laser"),
        ("Muzzle", muzzle, "NUM_Muzzle"),
        ("Grip", grip, "NUM_LeftHand"),
    ):
        ec = type(val)
        for nm in dir(ec):
            if nm.isupper() and getattr(ec, nm) == val:
                lines.append(f"  {label} -> {enum_name}::{nm}")
except Exception as exc:
    lines.append(f"ERR {exc}")

# test pin set formats on a throwaway make struct node in character BeginSetup
char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for g in unreal.BlueprintEditorLibrary.list_graphs(char):
    if g.get_name() != "BeginSetup":
        continue
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in ed.list_all_nodes():
        if node.get_name() != "K2Node_GenericCreateObject_2":
            continue
        pin = None
        for p in unreal.BlueprintEditorLibrary.list_all_pins(node):
            if str(unreal.BlueprintGraphPinLibrary.get_pin_name(p)).startswith("ItemData_Attachments"):
                pin = p
                break
        if not pin:
            continue
        formats = [
            "(Sight_37_688233D743AA415C91250EBC240B11ED=NewEnumerator1,Laser_38_3209213B48BBF0256E8473A33CC4C0FE=NewEnumerator1,Muzzle_42_288332C341D7A8B7E31632867A1FE4DB=NewEnumerator1,Grip_46_62A21AB489496DC33D1ACDA661CA2D84=NewEnumerator0)",
            "(Sight_37_688233D743AA415C91250EBC240B11ED=HOLOSIGHT,Laser_38_3209213B48BBF0256E8473A33CC4C0FE=LASER,Muzzle_42_288332C341D7A8B7E31632867A1FE4DB=SUPRESSOR,Grip_46_62A21AB489496DC33D1ACDA661CA2D84=NORMAL)",
            "(Sight_37_688233D743AA415C91250EBC240B11ED=NUM_Sights::HOLOSIGHT,Laser_38_3209213B48BBF0256E8473A33CC4C0FE=NUM_Laser::LASER,Muzzle_42_288332C341D7A8B7E31632867A1FE4DB=NUM_Muzzle::SUPRESSOR,Grip_46_62A21AB489496DC33D1ACDA661CA2D84=NUM_LeftHand::NORMAL)",
        ]
        for fmt in formats:
            pin.set_pin_value(fmt)
            got = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            lines.append(f"format {fmt[:40]}... -> {got}")

OUT.write_text("\n".join(lines))
