"""Probe BP_Scope and scope material params for ring size."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_scope_ring.log")
lines = []

scope = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Attachments/Scope/Blueprints/BP_Scope.BP_Scope")
scdo = unreal.get_default_object(scope.generated_class())
lines.append("=== BP_Scope CDO ===")
for prop in sorted(dir(scdo)):
    if prop.startswith("_"):
        continue
    lower = prop.lower()
    if any(k in lower for k in ("scope", "render", "radius", "glass", "mesh", "material", "sight", "gradient", "distance")):
        try:
            v = scdo.get_editor_property(prop)
            lines.append(f"  {prop}={v.get_name() if hasattr(v,'get_name') else v!r}")
        except Exception:
            pass

for g in unreal.BlueprintEditorLibrary.list_graphs(scope):
    if g.get_name() != "Aim":
        continue
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append("\n=== BP_Scope Aim graph ===")
    for node in ed.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if any(k in title for k in ("ScopeRadius", "Gradient", "Sight", "Render", "Visibility", "Material")):
            lines.append(f"  {node.get_name()} | {title}")
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                if val:
                    lines.append(f"    {pn}={val}")

sniper = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper"
)
cdo = unreal.get_default_object(sniper.generated_class())
lines.append("\n=== Sniper current ===")
for prop in ("AimDistanceFromCamera", "ScopeMat_SightDistance", "ScopeMat_GradientParam"):
    lines.append(f"  {prop}={cdo.get_editor_property(prop)!r}")

char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))
for node in eg.list_all_nodes():
    if node.get_name() != "K2Node_Select_5":
        continue
    lines.append("\n=== Select_5 FOV ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
        if val and pn.startswith("NewEnumerator"):
            lines.append(f"  {pn}={val}")

# original bodycam sniper from BODYCAMFPSKIT if accessible - compare file
import os
orig = "/Users/nickortiz/Documents/Unreal Projects/BODYCAMFPSKIT/Content/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.uasset"
lines.append(f"\norig sniper size={os.path.getsize(orig) if os.path.exists(orig) else 'missing'}")
scar = "/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Content/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.uasset"
lines.append(f"scar sniper size={os.path.getsize(scar)}")

OUT.write_text("\n".join(lines))
