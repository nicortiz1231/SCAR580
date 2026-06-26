"""Map NUM_Sights enum indices to switch branches."""
import unreal
from pathlib import Path

lines = []
pickup = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Pickup_Sniper.BP_Weapon_Pickup_Sniper")
cdo = unreal.get_default_object(pickup.generated_class())
ec = type(cdo.get_editor_property("Item Data AttachmentsSight"))
for name in sorted(dir(ec)):
    if name.isupper():
        val = getattr(ec, name)
        lines.append(f"NUM_Sights.{name} = {val} (index {int(val)})")

auto = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(auto))
sw = next(n for n in eg.list_all_nodes() if n.get_name() == "K2Node_SwitchEnum_1")
for pin in unreal.BlueprintEditorLibrary.list_all_pins(sw):
    pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
    if not pn.startswith("NewEnumerator"):
        continue
    linked = [str(lp.get_owning_node().get_node_title()).replace("\n"," ") for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
    lines.append(f"switch {pn} -> {linked or 'OPEN'}")

# test SCOPE pin text
char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for g in unreal.BlueprintEditorLibrary.list_graphs(char):
    if g.get_name() != "BeginSetup":
        continue
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in ed.list_all_nodes():
        if node.get_name() != "K2Node_GenericCreateObject_2":
            continue
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            if not str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin)).startswith("ItemData_Attachments"):
                continue
            for fmt in (
                "(Sight_37_688233D743AA415C91250EBC240B11ED=SCOPE,Laser_38_3209213B48BBF0256E8473A33CC4C0FE=LASER,Muzzle_42_288332C341D7A8B7E31632867A1FE4DB=SUPRESSOR,Grip_46_62A21AB489496DC33D1ACDA661CA2D84=NORMAL)",
                "(Sight_37_688233D743AA415C91250EBC240B11ED=NewEnumerator2,Laser_38_3209213B48BBF0256E8473A33CC4C0FE=NewEnumerator0,Muzzle_42_288332C341D7A8B7E31632867A1FE4DB=NewEnumerator0,Grip_46_62A21AB489496DC33D1ACDA661CA2D84=NewEnumerator0)",
            ):
                pin.set_pin_value(fmt)
                lines.append(f"pin set -> {unreal.BlueprintGraphPinLibrary.get_pin_value(pin)}")

Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sights_scope_enum.log").write_text("\n".join(lines))
