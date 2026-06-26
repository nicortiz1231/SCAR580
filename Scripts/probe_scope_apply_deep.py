"""Deep search attachment mesh apply across all character/item graphs."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_scope_apply_deep.log")
lines = []

def scan_bp(path, label):
    bp = unreal.load_asset(path)
    if not bp:
        return
    for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
        editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
        for node in editor.list_all_nodes():
            title = str(node.get_node_title()).replace("\n", " | ")
            cls = node.get_class().get_name()
            blob = f"{title} {node.get_name()} {cls}"
            if any(k in blob for k in (
                "SetStaticMesh", "ScopeSightMesh", "OpticSightMesh", "SpawnAttachment",
                "Switch on ENUM_Sights", "SetVisibility", "Scope", "Sight",
            )):
                lines.append(f"[{label}/{g.get_name()}] {node.get_name()} | {title}")
                for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                    pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                    if pn in ("self", "NewMesh", "Selection", "execute", "then", "bNewVisibility"):
                        linked = []
                        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                            o = lp.get_owning_node()
                            linked.append(str(o.get_node_title()).replace("\n"," | "))
                        try:
                            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                            if val:
                                linked.append(val)
                        except Exception:
                            pass
                        if linked:
                            lines.append(f"    {pn} -> {linked}")

scan_bp("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter", "char")
scan_bp("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base", "item")
scan_bp("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper", "sniper")

# Akimbo spawner sight branch detail
item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    if g.get_name() != "Akimbo Spawner":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append("=== Akimbo Spawner OpticSight chain ===")
    for node in editor.list_all_nodes():
        if node.get_name() not in ("K2Node_VariableGet_171", "K2Node_VariableSet_30", "K2Node_AddComponent_3"):
            continue
        lines.append(f"  {node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if pn in ("execute", "then", "self", "ReturnValue"):
                linked = []
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                    linked.append(lp.get_owning_node().get_name())
                if linked:
                    lines.append(f"    {pn} -> {linked}")

OUT.write_text("\n".join(lines))
