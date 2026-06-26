import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_swap_itemdata.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(bp)
)

for start in ("K2Node_VariableGet_133", "K2Node_VariableGet_83", "K2Node_VariableSet_0", "K2Node_VariableSet_59"):
    for node in editor.list_all_nodes():
        if node.get_name() != start:
            continue
        lines.append(f"=== {start} | {str(node.get_node_title()).replace(chr(10),' | ')} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            linked = []
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                o = lp.get_owning_node()
                linked.append(f"{o.get_name()}:{pname}")
            try:
                val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                if val:
                    linked.append(val)
            except Exception:
                pass
            if linked:
                lines.append(f"  {pname} -> {linked}")

# search SetWeaponAmmoData calls on character
for node in editor.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    if "SetWeaponAmmoData" in title or "Set ItemData" in title or title == "Set ItemData":
        lines.append(f"=== {node.get_name()} | {title} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if pname in ("execute", "then", "self"):
                linked = []
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                    o = lp.get_owning_node()
                    linked.append(o.get_name())
                if linked:
                    lines.append(f"  {pname} -> {linked}")

OUT.write_text("\n".join(lines))
