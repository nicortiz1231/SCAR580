"""Find ItemData assignment to spawned weapon on character."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_itemdata_assign.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(bp)
)

for node in editor.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    cls = node.get_class().get_name()
    if cls == "K2Node_CallFunction":
        for prop in ("function_reference",):
            try:
                ref = str(node.get_editor_property(prop))
                if any(k in ref for k in ("ItemData", "Attachment", "WeaponAmmo", "SpawnAttachment")):
                    lines.append(f"{node.get_name()} | {title} | {ref}")
            except Exception:
                pass
    if "ItemData" in title or "WeaponAmmo" in title:
        lines.append(f"{node.get_name()} | {title}")

# BreakStruct_9 connections
for node in editor.list_all_nodes():
    if node.get_name() != "K2Node_BreakStruct_9":
        continue
    lines.append("=== BreakStruct_9 ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        linked = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            owner = lp.get_owning_node()
            linked.append(f"{owner.get_name()}:{pname}")
        try:
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            if val:
                linked.append(val)
        except Exception:
            pass
        if linked:
            lines.append(f"  {pname} -> {linked}")

OUT.write_text("\n".join(lines))
