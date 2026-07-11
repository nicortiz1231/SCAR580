"""Verify attachment property paths and SetWeaponAmmoData signature."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_weapon_attachment_api.log")
lines = []

char_cls = unreal.load_class(None, "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter_C")
item_cls = unreal.load_class(None, "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base_C")

for cls, label in ((char_cls, "CHAR"), (item_cls, "ITEM")):
    lines.append(f"=== {label} {cls.get_name()} ===")
    for prop in ("EquippedWeapon", "PrimarySlot", "SecondarySlot", "HandsSlot", "SpawnedItem", "ItemData"):
        try:
            field = cls.get_class().find_property_by_name(prop) if hasattr(cls.get_class(), "find_property_by_name") else None
        except Exception:
            field = None
        try:
            val = unreal.get_default_object(cls).get_editor_property(prop)
            lines.append(f"  {prop}={val!r} type={type(val).__name__}")
        except Exception as exc:
            lines.append(f"  {prop} ERR {exc}")

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for graph in unreal.BlueprintEditorLibrary.list_graphs(item):
    if graph.get_name() != "SetWeaponAmmoData":
        continue
    entry = None
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    for node in ed.list_all_nodes():
        if node.get_class().get_name() == "K2Node_FunctionEntry":
            entry = node
            break
    if entry:
        lines.append("SetWeaponAmmoData pins:")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(entry):
            lines.append(f"  {unreal.BlueprintGraphPinLibrary.get_pin_name(pin)}")

for enum_path in (
    "/Game/BodycamFPSKIT/Blueprints/Enums/ENUM_Sights",
    "/Game/BodycamFPSKIT/Blueprints/Enums/ENUM_Laser",
    "/Game/BodycamFPSKIT/Blueprints/Enums/ENUM_Muzzle",
    "/Game/BodycamFPSKIT/Blueprints/Enums/ENUM_LeftHand",
):
    enum_cls = unreal.load_class(None, f"{enum_path}.{enum_path.split('/')[-1]}")
    lines.append(f"=== {enum_path.split('/')[-1]} ===")
    if enum_cls:
        for name in dir(enum_cls):
            if name.isupper():
                try:
                    lines.append(f"  {name}={int(getattr(enum_cls, name))}")
                except Exception:
                    pass

OUT.write_text("\n".join(lines))
