import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_cf46_props.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(bp)
)
for node in editor.list_all_nodes():
    if node.get_name() != "K2Node_CallFunction_46":
        continue
    for prop in sorted(dir(node)):
        if prop.startswith("_") or "pin" in prop.lower():
            continue
        try:
            val = node.get_editor_property(prop.replace("_", " ") if False else prop)
            if val is not None and str(val):
                lines.append(f"{prop}={val!r}")
        except Exception:
            pass

OUT.write_text("\n".join(lines))
