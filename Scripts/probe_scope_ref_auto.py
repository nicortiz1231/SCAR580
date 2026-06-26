"""Trace ScopeRef assignment in AutomaticBase sight switch."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_scope_ref_auto.log")
lines = []

auto = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase"
)
for g in unreal.BlueprintEditorLibrary.list_graphs(auto):
    if g.get_name() != "EventGraph":
        continue
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in ed.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if any(k in title for k in ("ScopeRef", "Set ScopeRef", "BP_Scope", "SpawnActor", "NewEnumerator7", "Switch on ENUM_Sights")):
            lines.append(f"{node.get_name()} | {title}")
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
                if val or linked or pn.startswith("NewEnumerator") or pn in ("then", "execute", "ReturnValue"):
                    lines.append(f"  {pn} val={val!r} linked={linked}")

# BP_Scope Aim graph
scope = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Attachments/Scope/Blueprints/BP_Scope.BP_Scope")
for g in unreal.BlueprintEditorLibrary.list_graphs(scope):
    if g.get_name() != "Aim":
        continue
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append(f"\n=== BP_Scope Aim graph ===")
    for node in ed.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        lines.append(f"  {node.get_name()} | {title}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            if val:
                lines.append(f"    {pn}={val}")

# sniper BeginPlay scope mesh
sniper = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper"
)
for g in unreal.BlueprintEditorLibrary.list_graphs(sniper):
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in ed.list_all_nodes():
        title = str(node.get_node_title())
        if "ScopeRef" in title or "SpawnActor" in title:
            lines.append(f"\n[sniper/{g.get_name()}] {node.get_name()} | {title.replace(chr(10),' | ')}")

OUT.write_text("\n".join(lines))
