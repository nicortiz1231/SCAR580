"""Full BreakStruct_11 output wiring."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_attach_outputs.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(bp)
)

for node in editor.list_all_nodes():
    if node.get_name() not in ("K2Node_BreakStruct_11", "K2Node_SwitchEnum_3", "K2Node_SwitchEnum_4"):
        continue
    lines.append(f"=== {node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')} ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        linked = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            owner = lp.get_owning_node()
            linked.append(f"{owner.get_name()}:{pname}")
        try:
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            if val:
                linked.append(f"val={val!r}")
        except Exception:
            pass
        if linked or pname.startswith("NewEnumerator") or "Sight" in pname or "execute" in pname:
            lines.append(f"  {pname} -> {linked}")

OUT.write_text("\n".join(lines))
