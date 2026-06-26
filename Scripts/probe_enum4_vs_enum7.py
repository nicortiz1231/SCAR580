"""Full exec chains for ENUM_Sights enum4 vs enum7 in AutomaticBase."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_enum4_vs_enum7.log")
lines = []

auto = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase"
)
ed = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(auto)
)

switch = None
for node in ed.list_all_nodes():
    if node.get_name() == "K2Node_SwitchEnum_1":
        switch = node
        break

def walk_exec(start_pin, label, depth=0, seen=None):
    if not start_pin or depth > 20:
        return
    if seen is None:
        seen = set()
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(start_pin):
        if lp.get_pin_direction() != unreal.EdGraphPinDirection.EGPD_INPUT:
            continue
        o = lp.get_owning_node()
        nid = o.get_name()
        if nid in seen:
            continue
        seen.add(nid)
        title = str(o.get_node_title()).replace("\n", " | ")
        lines.append(f"{'  '*depth}[{label}] {nid} | {title}")
        then = o.find_output_pin("then")
        if then:
            walk_exec(then, label, depth + 1, seen)

if switch:
    for enum in ("NewEnumerator4", "NewEnumerator7"):
        pin = switch.find_output_pin(enum)
        lines.append(f"\n=== {enum} chain ===")
        if pin:
            walk_exec(pin, enum)

# BP_Scope CDO props
scope = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Attachments/Scope/Blueprints/BP_Scope.BP_Scope")
scdo = unreal.get_default_object(scope.generated_class())
lines.append("\n=== BP_Scope CDO ===")
for prop in sorted(dir(scdo)):
    if prop.startswith("_"):
        continue
    if any(k in prop.lower() for k in ("scope", "render", "radius", "glass", "mesh", "material")):
        try:
            v = scdo.get_editor_property(prop)
            lines.append(f"  {prop}={v.get_name() if hasattr(v,'get_name') else v!r}")
        except Exception:
            pass

OUT.write_text("\n".join(lines))
