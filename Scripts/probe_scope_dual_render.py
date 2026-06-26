"""Deep probe: scope spawn, Aim params, BP_Scope state, FOV path."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_scope_dual_render.log")
lines = []

char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))

# ScopeRef variable get + Aim call pins
for name in ("K2Node_VariableGet_81", "K2Node_VariableGet_142", "K2Node_VariableGet_151",
             "K2Node_CallFunction_128", "K2Node_SpawnActorFromClass_2"):
    for node in eg.list_all_nodes():
        if node.get_name() != name:
            continue
        lines.append(f"\n=== {name} | {str(node.get_node_title()).replace(chr(10),' | ')} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
            if val or linked or pn in ("execute", "then", "self", "Class", "On/Off", "GradientParam", "SightDistance", "ReturnValue"):
                lines.append(f"  {pn} val={val!r} linked={linked}")

# AutomaticBase scope spawn enum7
auto = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase")
for g in unreal.BlueprintEditorLibrary.list_graphs(auto):
    if "Material" not in g.get_name() and "Reload" not in g.get_name():
        continue
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in ed.list_all_nodes():
        t = str(node.get_node_title())
        if any(k in t for k in ("BP_Scope", "ScopeRef", "SpawnActor", "NewEnumerator7")):
            lines.append(f"\n[{g.get_name()}] {node.get_name()} | {t.replace(chr(10),' ')[:70]}")
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                if val and ("Scope" in pn or "Class" in pn or "Enumerator7" in pn):
                    lines.append(f"    {pn}={val}")

sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
cdo = unreal.get_default_object(sniper.generated_class())
lines.append("\n=== Sniper CDO ===")
for p in ("AimDistanceFromCamera", "ScopeMat_SightDistance", "ScopeMat_GradientParam", "ScopeRenderRadius"):
    lines.append(f"  {p}={cdo.get_editor_property(p)}")

# Select FOV
for node in eg.list_all_nodes():
    if node.get_name() == "K2Node_Select_5":
        pin = node.find_input_pin("NewEnumerator14")
        lines.append(f"\nSelect_5 NewEnumerator14={unreal.BlueprintGraphPinLibrary.get_pin_value(pin) if pin else '?'}")

# Character HandsSlot attachment enum
for g in unreal.BlueprintEditorLibrary.list_graphs(char):
    if g.get_name() != "BeginSetup":
        continue
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in ed.list_all_nodes():
        if node.get_name() != "K2Node_GenericCreateObject_2":
            continue
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            if val and "Attachment" in pn:
                lines.append(f"\nHandsSlot {pn}={val}")

OUT.write_text("\n".join(lines))
