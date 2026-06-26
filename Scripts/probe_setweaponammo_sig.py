"""SetWeaponAmmoData function signature and exec flow."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_setweaponammo_sig.log")
lines = []

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    if g.get_name() != "SetWeaponAmmoData":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        if node.get_class().get_name() != "K2Node_FunctionEntry":
            continue
        lines.append("=== FunctionEntry pins ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
            lines.append(f"  {pn} dir={unreal.BlueprintGraphPinLibrary.get_pin_direction(pin)} linked={linked}")
        then = node.find_output_pin("then")
        stack = [(then, 0)]
        lines.append("=== Exec chain ===")
        while stack:
            pin, depth = stack.pop()
            if not pin or depth > 40:
                continue
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                if lp.get_pin_direction() != unreal.EdGraphPinDirection.EGPD_INPUT:
                    continue
                o = lp.get_owning_node()
                t = str(o.get_node_title()).replace("\n", " | ")
                lines.append(f"{'  '*depth}{o.get_name()} | {t}")
                nxt = o.find_output_pin("then")
                if nxt:
                    stack.append((nxt, depth + 1))

# Compare original vs SCAR sniper event graph node count
for label, proj in (("SCAR", "/Users/nickortiz/Documents/Unreal Projects/SCAR-580/SCAR.uproject"),
                    ("ORIG", "/Users/nickortiz/Documents/Unreal Projects/BODYCAMFPSKIT/BODYCAMFPSKIT.uproject")):
    pass

sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(sniper))
lines.append(f"\n=== SCAR sniper EventGraph {len(eg.list_all_nodes())} nodes ===")
for node in eg.list_all_nodes():
    lines.append(f"  {node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')}")

OUT.write_text("\n".join(lines))
