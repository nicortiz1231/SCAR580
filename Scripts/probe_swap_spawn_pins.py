import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_swap_spawn_pins.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(bp)
)

for name in ("K2Node_SpawnActorFromClass_1", "K2Node_SpawnActorFromClass_3", "K2Node_SpawnActorFromClass_2"):
    for node in editor.list_all_nodes():
        if node.get_name() != name:
            continue
        lines.append(f"=== {name} | {str(node.get_node_title()).replace(chr(10),' | ')} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if "Attach" in pname or "Item" in pname or "Sight" in pname or pname in ("Class", "execute", "then"):
                linked = []
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                    o = lp.get_owning_node()
                    linked.append(o.get_name())
                try:
                    val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                    if val:
                        linked.append(val)
                except Exception:
                    pass
                lines.append(f"  {pname} -> {linked}")

OUT.write_text("\n".join(lines))
