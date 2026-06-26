"""Dump ENUM_ItemSlots and character slot defaults from live CDO after map load."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_enum_slots_full.log")
lines = []


def log(msg: str) -> None:
    lines.append(msg)
    unreal.log(msg)


# Load enum asset
for path in (
    "/Game/BodycamFPSKIT/Blueprints/Enums/ENUM_ItemSlots",
    "/Game/BodycamFPSKIT/Blueprints/ENUM_ItemSlots",
):
    obj = unreal.load_asset(path)
    if obj:
        log(f"ENUM asset {path} type={type(obj)}")
        for name in sorted(dir(obj)):
            if not name.startswith("_"):
                try:
                    v = getattr(obj, name)
                    if isinstance(v, int) or "Enumerator" in name or name.isupper():
                        log(f"  {name}={v!r}")
                except Exception:
                    pass

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)

for node in editor.list_all_nodes():
  if node.get_class().get_name() == "K2Node_Select":
      title = str(node.get_node_title()).replace("\n", " | ")
      log(f"SELECT {node.get_name()} | {title}")
      for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
          pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
          if not pname.startswith("NewEnumerator") and pname not in ("Index", "ReturnValue"):
              continue
          linked = []
          for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
              owner = lp.get_owning_node()
              linked.append(f"{owner.get_name()}:{str(unreal.BlueprintGraphPinLibrary.get_pin_name(lp))}")
          default = ""
          try:
              default = f" default={pin.get_default_as_string()!r}"
          except Exception:
              pass
          log(f"  {pname}{default} -> {linked}")

for node in editor.list_all_nodes():
    if node.get_class().get_name() == "K2Node_CastByteToEnum":
        log(f"CAST {node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')}")

# Inspect BP_Item_Base for ItemSlot / weapon class
item_base = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
if item_base:
    cdo = unreal.get_default_object(item_base.generated_class())
    log("BP_Item_Base CDO:")
    for name in dir(cdo):
        lower = name.lower()
        if any(k in lower for k in ("slot", "type", "enum", "weapon", "item")):
            try:
                val = cdo.get_editor_property(name)
                if val is not None and val != "":
                    log(f"  {name}={val!r}")
            except Exception:
                pass

# Sniper weapon CDO all properties
sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
if sniper:
    cdo = unreal.get_default_object(sniper.generated_class())
    log("BP_Weapon_Sniper CDO:")
    for name in sorted(dir(cdo)):
        if name.startswith("_"):
            continue
        try:
            val = cdo.get_editor_property(name)
            if val is not None and val != "" and val is not False:
                log(f"  {name}={val!r}")
        except Exception:
            pass

OUT.write_text("\n".join(lines))
