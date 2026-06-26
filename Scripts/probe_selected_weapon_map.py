"""Trace SelectedWeapon index -> equipped weapon mapping."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_selected_weapon_map.log")
lines = []


def log(msg: str) -> None:
    lines.append(msg)
    unreal.log(msg)


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)

for node in editor.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    name = node.get_name()
    if "SelectedWeapon" in title or "Switch" in title and "ENUM" in title:
        log(f"{name} | {title}")
    if name in (
        "K2Node_SwitchEnum_0",
        "K2Node_Switch_0",
        "K2Node_Select_0",
        "K2Node_VariableSet_36",
        "K2Node_VariableSet_55",
        "K2Node_VariableSet_140",
        "K2Node_IfThenElse_19",
        "K2Node_CallFunction_95",
        "K2Node_CallFunction_340",
        "K2Node_SpawnActorFromClass_2",
    ):
        log(f"=== {name} | {title} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            direction = unreal.BlueprintGraphPinLibrary.get_pin_direction(pin)
            dir_s = "IN" if direction == unreal.EdGraphPinDirection.EGPD_INPUT else "OUT"
            linked = []
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                owner = lp.get_owning_node()
                linked.append(f"{owner.get_name()}:{str(unreal.BlueprintGraphPinLibrary.get_pin_name(lp))}")
            default = ""
            try:
                default = f" default={pin.get_default_as_string()!r}"
            except Exception:
                pass
            log(f"  {dir_s} {pname}{default} -> {linked}")

# BeginPlay spawn chain
begin = editor.find_event_node("ReceiveBeginPlay")
log("BeginPlay chain:")
stack = [begin.find_then_pin()] if begin else []
depth = 0
while stack and depth < 12:
    pin = stack.pop()
    if not pin:
        continue
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
        owner = lp.get_owning_node()
        t = str(owner.get_node_title()).replace("\n", " | ")
        log(f"  {'  '*depth}{owner.get_name()} | {t}")
        for out in (owner.find_then_pin(),):
            if out:
                stack.append(out)
        if owner.get_class().get_name() == "K2Node_ExecutionSequence":
            for p in unreal.BlueprintEditorLibrary.list_all_pins(owner):
                pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(p))
                if pn.startswith("then_"):
                    stack.append(p)
    depth += 1

# Inspect BP_Item_Base or weapon item class for slot type
for path in unreal.EditorAssetLibrary.list_assets("/Game/BodycamFPSKIT/Blueprints", recursive=True):
    if "BP_Weapon_Sniper" in path or "BP_Item" in path:
        if path.endswith("BP_Weapon_Sniper") or "BP_Item_Base" in path:
            log(f"PATH {path}")

# Compare rifle/pistol/sniper weapon blueprints for slot enum property
for path in (
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Pistol/BP_Weapon_Pistol.BP_Weapon_Pistol",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/AmericanRifle/BP_Weapon_AmericanRifle.BP_Weapon_AmericanRifle",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper",
):
    asset = unreal.load_asset(path)
    if not asset:
        log(f"MISSING {path}")
        continue
    cdo = unreal.get_default_object(asset.generated_class())
    log(f"=== {path.split('/')[-1]} ===")
    for prop in dir(cdo):
        lower = prop.lower()
        if any(k in lower for k in ("slot", "weapon", "item", "enum", "type")):
            try:
                val = cdo.get_editor_property(prop)
                if val is not None and val != "" and val is not False:
                    log(f"  {prop}={val!r}")
            except Exception:
                pass

OUT.write_text("\n".join(lines))
