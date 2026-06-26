"""Read exact attachment struct text from pickup sniper."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_pickup_attach_text.log")
lines = []

pickup = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Pickup_Sniper.BP_Weapon_Pickup_Sniper")
cdo = unreal.get_default_object(pickup.generated_class())

for prop_name in dir(cdo):
    if "attach" in prop_name.lower() or "item" in prop_name.lower():
        pass

# try common property names
for name in (
    "ItemData", "Item Data", "DefaultItemData", "ST_Item",
):
    try:
        val = cdo.get_editor_property(name)
        lines.append(f"{name}={val}")
    except Exception as exc:
        lines.append(f"{name} ERR {exc}")

# scan all editor properties
try:
    for prop in cdo.get_class().properties():
        pn = prop.get_name()
        if any(k in pn.lower() for k in ("item", "attach", "sight", "ammo")):
            try:
                lines.append(f"prop {pn}={cdo.get_editor_property(pn)}")
            except Exception as exc:
                lines.append(f"prop {pn} ERR {exc}")
except Exception as exc:
    lines.append(f"properties ERR {exc}")

# pickup event graph ItemData pins
for g in unreal.BlueprintEditorLibrary.list_graphs(pickup):
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in ed.list_all_nodes():
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            val = str(unreal.BlueprintGraphPinLibrary.get_pin_value(pin))
            if val and "Attachments" in pname:
                lines.append(f"[{g.get_name()}] {node.get_name()} {pname}={val}")

OUT.write_text("\n".join(lines))
