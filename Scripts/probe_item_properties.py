"""List BP_Item_Base properties related to item data."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_item_properties.log")
lines = []

item_cls = unreal.load_class(None, "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base_C")
cdo = unreal.get_default_object(item_cls)

for prop in dir(cdo):
    if any(k in prop.lower() for k in ("item", "ammo", "attach", "spawn")):
        try:
            val = cdo.get_editor_property(prop)
            lines.append(f"{prop}={val!r}")
        except Exception as exc:
            lines.append(f"{prop} ERR {exc}")

# also try ST_Item struct fields via HandsSlot on character CDO in PIE defaults
char = unreal.load_class(None, "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter_C")
char_cdo = unreal.get_default_object(char)
for slot in ("PrimarySlot", "HandsSlot"):
    try:
        slot_val = char_cdo.get_editor_property(slot)
        lines.append(f"\n{slot}={slot_val!r}")
        if slot_val:
            for prop in dir(slot_val):
                if not prop.startswith("_"):
                    try:
                        lines.append(f"  {slot}.{prop}={slot_val.get_editor_property(prop)!r}")
                    except Exception:
                        pass
    except Exception as exc:
        lines.append(f"{slot} ERR {exc}")

OUT.write_text("\n".join(lines))
