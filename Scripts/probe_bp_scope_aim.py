"""Full BP_Scope Aim graph dump."""
import unreal
from pathlib import Path
OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_bp_scope_aim.log")
lines = []
scope = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Attachments/Scope/Blueprints/BP_Scope.BP_Scope")
for g in unreal.BlueprintEditorLibrary.list_graphs(scope):
    if g.get_name() != "Aim":
        continue
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in ed.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        lines.append(f"{node.get_name()} | {title}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
            if val or linked:
                lines.append(f"  {pn} val={val!r} linked={linked}")
scdo = unreal.get_default_object(scope.generated_class())
lines.append("\n=== all CDO props with numeric values ===")
for prop in sorted(dir(scdo)):
    if prop.startswith("_"):
        continue
    try:
        v = scdo.get_editor_property(prop)
        if isinstance(v, (int, float)) or (hasattr(v, "x") and not hasattr(v, "pitch")):
            lines.append(f"  {prop}={v!r}")
    except Exception:
        pass
OUT.write_text("\n".join(lines))
