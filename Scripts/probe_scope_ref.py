"""Check if sniper has ScopeRef / BP_Scope vs static mesh scope path."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_scope_ref.log")
lines = []

sniper = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper"
)
cdo = unreal.get_default_object(sniper.generated_class())
for prop in sorted(dir(cdo)):
    if prop.startswith("_"):
        continue
    if "scope" in prop.lower() or "sight" in prop.lower():
        try:
            v = cdo.get_editor_property(prop)
            lines.append(f"CDO {prop}={v!r}")
        except Exception:
            pass

# AutomaticBase enum7 path detail
auto = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase"
)
for g in unreal.BlueprintEditorLibrary.list_graphs(auto):
    if g.get_name() != "EventGraph":
        continue
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in ed.list_all_nodes():
        if node.get_name() != "K2Node_SwitchEnum_1":
            continue
        pin = node.find_output_pin("NewEnumerator7")
        if not pin:
            continue
        lines.append("\n=== AutomaticBase NewEnumerator7 chain ===")
        cur = pin
        for _ in range(15):
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(cur):
                if lp.get_pin_direction() != unreal.EdGraphPinDirection.EGPD_INPUT:
                    continue
                o = lp.get_owning_node()
                lines.append(f"  -> {o.get_name()} | {str(o.get_node_title()).replace(chr(10),' | ')}")
                then = o.find_output_pin("then")
                if then:
                    nxt = [x for x in unreal.BlueprintGraphPinLibrary.list_connected_pins(then) if x.get_pin_direction()==unreal.EdGraphPinDirection.EGPD_INPUT]
                    if nxt:
                        o = nxt[0].get_owning_node()
                        lines.append(f"  -> {o.get_name()} | {str(o.get_node_title()).replace(chr(10),' | ')}")
                break
            break

# trace VariableGet_81 backward on exec
char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))
for node in eg.list_all_nodes():
    if node.get_name() != "K2Node_VariableGet_81":
        continue
    lines.append("\n=== VariableGet_81 exec inputs ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) != unreal.EdGraphPinDirection.EGPD_INPUT:
            continue
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        if pn != "execute":
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            o = lp.get_owning_node()
            lines.append(f"  exec <- {o.get_name()} | {str(o.get_node_title()).replace(chr(10),' | ')}")

# BP_Scope class
scope_bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Attachments/Scope/Blueprints/BP_Scope.BP_Scope")
if scope_bp:
    lines.append(f"\nBP_Scope loaded={scope_bp.get_name()}")
    scdo = unreal.get_default_object(scope_bp.generated_class())
    for prop in sorted(dir(scdo)):
        if prop.startswith("_"):
            continue
        if "scope" in prop.lower() or "sight" in prop.lower() or "mesh" in prop.lower():
            try:
                lines.append(f"  {prop}={scdo.get_editor_property(prop)!r}")
            except Exception:
                pass

OUT.write_text("\n".join(lines))
