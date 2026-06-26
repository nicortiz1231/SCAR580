import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sight_switch.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(bp)
)

for sw_name in ("K2Node_SwitchEnum_3", "K2Node_SwitchEnum_4"):
    for node in editor.list_all_nodes():
        if node.get_name() != sw_name:
            continue
        lines.append(f"=== {sw_name} | {str(node.get_node_title()).replace(chr(10),' | ')} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if not (pn.startswith("NewEnumerator") or pn in ("Selection", "execute")):
                continue
            linked = []
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                o = lp.get_owning_node()
                linked.append(f"{o.get_name()} | {str(o.get_node_title()).replace(chr(10),' | ')}")
            try:
                val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                if val:
                    linked.append(f"val={val!r}")
            except Exception:
                pass
            lines.append(f"  {pn} -> {linked}")

for cf in ("K2Node_CallFunction_43", "K2Node_CallFunction_44", "K2Node_CallFunction_193"):
    for node in editor.list_all_nodes():
        if node.get_name() != cf:
            continue
        lines.append(f"=== {cf} | {str(node.get_node_title()).replace(chr(10),' | ')} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if pn in ("execute", "then", "self", "NewMesh", "Target"):
                linked = []
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                    o = lp.get_owning_node()
                    linked.append(f"{o.get_name()}:{pn}")
                if linked:
                    lines.append(f"  {pn} -> {linked}")

OUT.write_text("\n".join(lines))
