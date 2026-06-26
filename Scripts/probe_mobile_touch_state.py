"""Probe mobile touch vars and weapon swipe state."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_mobile_touch_state.log")
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
    if any(
        k in title
        for k in (
            "Weapon Swipe",
            "WeaponSwipe",
            "Mobile Touch",
            "GetInputTouchState",
            "SwapWeapon",
            "IA_PrimarySlot",
            "IA_SecondarySlot",
            "MobileTouch",
        )
    ):
        log(f"{name} | {title}")
        if node.get_class().get_name() == "K2Node_Comment":
            try:
                log(f"  comment={node.get_editor_property('node_comment')!r}")
            except Exception:
                pass
        if "IfThenElse" in node.get_class().get_name() and "Weapon" not in title:
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                if pname in ("execute", "then", "else"):
                    linked = []
                    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                        owner = lp.get_owning_node()
                        linked.append(f"{owner.get_name()}:{str(unreal.BlueprintGraphPinLibrary.get_pin_name(lp))}")
                    log(f"  {pname} -> {linked}")

tick = editor.find_event_node("ReceiveTick")
log("ReceiveTick chain:")
for linked in unreal.BlueprintGraphPinLibrary.list_connected_pins(tick.find_then_pin()):
    owner = linked.get_owning_node()
    log(f"  -> {owner.get_name()} | {str(owner.get_node_title()).replace(chr(10), ' | ')}")

names = unreal.BlueprintEditorLibrary.list_member_variable_names(bp)
for v in names:
    if "Weapon" in v or "Swipe" in v or "MobileTouch" in v or "Pressed" in v:
        log(f"VAR {v}")

OUT.write_text("\n".join(lines))
