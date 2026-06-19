import unreal
from pathlib import Path
LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_beginsetup_runtime.log")
lines = []
bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
begin = None
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if g.get_name() == "BeginSetup":
        begin = g
        break
editor = unreal.BlueprintGraphEditor.get_graph_editor(begin)
for node in editor.list_all_nodes():
    cls = node.get_class().get_name()
    extra = ""
    if hasattr(node, "get_class"):
        for prop in dir(node):
            if "member" in prop.lower() or "function" in prop.lower() or "variable" in prop.lower():
                pass
    for prop in ("MemberName", "member_name", "FunctionReference", "function_reference", "VariableReference", "variable_reference"):
        try:
            val = node.get_editor_property(prop)
            if val:
                extra += f" {prop}={val}"
        except Exception:
            pass
    if extra or cls in ("K2Node_CallFunction", "K2Node_VariableSet"):
        lines.append(f"{cls}{extra}")
LOG.write_text("\n".join(lines))
