"""Dump weapon swipe branch wiring and enum slot values."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_weapon_swipe_wiring.log")
lines = []


def log(msg: str) -> None:
    lines.append(msg)
    unreal.log(msg)


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)

TARGETS = {
    "K2Node_IfThenElse_7",
    "K2Node_IfThenElse_44",
    "K2Node_IfThenElse_45",
    "K2Node_ExecutionSequence_9",
}


def dump_node(node):
    name = node.get_name()
    title = str(node.get_node_title()).replace("\n", " | ")
    log(f"=== {name} | {title} ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pin_name = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
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
        log(f"  {dir_s} {pin_name}{default} -> {linked}")


for node in editor.list_all_nodes():
    if node.get_name() in TARGETS:
        dump_node(node)
    if node.get_class().get_name() == "K2Node_Comment":
        try:
            c = str(node.get_editor_property("node_comment"))
            if "Weapon Swipe" in c:
                log(f"COMMENT: {c}")
        except Exception:
            pass

# Enum equality B pin defaults
for node in editor.list_all_nodes():
    if node.get_name() in ("K2Node_EnumEquality_0", "K2Node_EnumEquality_6"):
        log(f"=== {node.get_name()} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if pname == "B":
                try:
                    log(f"  B default={pin.get_default_as_string()!r}")
                except Exception:
                    pass

# Item slot enum
for path in unreal.EditorAssetLibrary.list_assets("/Game", recursive=True, include_folder=False):
    if path.endswith("ENUM_ItemSlots") or "ENUM_ItemSlots" in path:
        log(f"enum path: {path}")

try:
    enum_cls = unreal.load_object(None, "/Game/BodycamFPSKIT/Blueprints/ENUM_ItemSlots.ENUM_ItemSlots")
    if enum_cls:
        for name in ("PRIMARY", "SECONDARY", "EMPTY", "NewEnumerator0", "NewEnumerator10"):
            try:
                log(f"ENUM {name}={int(getattr(enum_cls, name))}")
            except Exception as exc:
                log(f"ENUM {name} ERR {exc}")
except Exception as exc:
    log(f"enum load {exc}")

OUT.write_text("\n".join(lines))
