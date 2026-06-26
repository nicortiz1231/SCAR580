"""List slot variables, enum entries, and BeginSetup weapon wiring."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_character_slots.log")
lines = []


def log(msg: str) -> None:
    lines.append(msg)
    unreal.log(msg)


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")

for name in unreal.BlueprintEditorLibrary.list_member_variable_names(bp):
    if "slot" in name.lower() or "weapon" in name.lower():
        try:
            t = unreal.BlueprintEditorLibrary.get_member_variable_type(bp, name)
            log(f"VAR {name} type={t}")
        except Exception:
            log(f"VAR {name}")

enum_path = "/Game/BodycamFPSKIT/Blueprints/Enums/ENUM_ItemSlots.ENUM_ItemSlots"
enum_asset = unreal.load_asset(enum_path)
if enum_asset:
    log(f"ENUM {enum_path}")
    for prop in ("display_name_map", "names", "enumerators"):
        try:
            log(f"  {prop}={enum_asset.get_editor_property(prop)!r}")
        except Exception as exc:
            log(f"  {prop} ERR {exc}")
    try:
        for i in range(20):
            name = enum_asset.get_display_name_field_by_index(i)
            if name:
                log(f"  enum[{i}] display={name}")
    except Exception as exc:
        log(f"  get_display_name_field_by_index ERR {exc}")

subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
for handle in subsystem.k2_gather_subobject_data_for_blueprint(bp):
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
    if not obj:
        continue
    cls = obj.get_class().get_name()
    if "Item" in cls or "Weapon" in cls or "Slot" in obj.get_name():
        log(f"SUBOBJ {obj.get_name()} | {cls}")
        for prop in sorted(dir(obj)):
            if prop.startswith("_"):
                continue
            lower = prop.lower()
            if any(k in lower for k in ("pickup", "weapon", "class", "ref", "item", "type", "slot")):
                try:
                    val = obj.get_editor_property(prop)
                    if val is not None and val != "" and val is not False:
                        if hasattr(val, "get_path_name"):
                            log(f"    {prop}={val.get_path_name()}")
                        else:
                            log(f"    {prop}={val!r}")
                except Exception:
                    pass

# BeginSetup graph nodes mentioning slot/weapon/sniper
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if g.get_name() != "BeginSetup":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if any(k in title for k in ("Slot", "Weapon", "Sniper", "Pistol", "Rifle", "Hands", "Primary", "Secondary")):
            log(f"BeginSetup {node.get_name()} | {title}")

OUT.write_text("\n".join(lines))
