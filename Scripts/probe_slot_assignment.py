"""Find where PrimarySlot/SecondarySlot are assigned."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_slot_assignment.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if any(k in title for k in ("Set PrimarySlot", "Set SecondarySlot", "Set MeleeSlot", "Set HandsSlot", "Construct Object")):
            lines.append(f"[{g.get_name()}] {node.get_name()} | {title}")
            if "Construct Object" in title:
                for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                    pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                    if pname == "Class":
                        try:
                            lines.append(f"  Class default={pin.get_default_as_string()!r}")
                        except Exception:
                            pass
            if "Set " in title and "Slot" in title:
                for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                    pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                    if pname.endswith("Slot"):
                        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                            owner = lp.get_owning_node()
                            lines.append(f"  {pname} <- {owner.get_name()} | {str(owner.get_node_title()).replace(chr(10),' | ')}")

# Compare pistol/rifle item class on construct
for path, label in (
    ("/Game/BodycamFPSKIT/Blueprints/Interactables/Pistol/BP_Weapon_Pistol.BP_Weapon_Pistol", "pistol"),
    ("/Game/BodycamFPSKIT/Blueprints/Interactables/AmericanRifle/BP_Weapon_AmericanRifle.BP_Weapon_AmericanRifle", "rifle"),
    ("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper", "sniper"),
):
    cls = unreal.load_class(None, path)
    lines.append(f"CLASS {label}={cls.get_path_name() if cls else None}")

OUT.write_text("\n".join(lines))
