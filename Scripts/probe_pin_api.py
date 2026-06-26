import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_pin_api.log")
lines = []

for cls_name in ("BlueprintGraphPinLibrary", "BlueprintGraphEditor", "BlueprintEditorLibrary", "K2Node_GenericCreateObject"):
    cls = getattr(unreal, cls_name, None)
    if not cls:
        lines.append(f"MISSING {cls_name}")
        continue
    lines.append(f"=== {cls_name} ===")
    for fn in sorted(dir(cls)):
        if fn.startswith("_"):
            continue
        if any(k in fn.lower() for k in ("default", "class", "object", "pin", "connect", "spawn", "create")):
            lines.append(f"  {fn}")

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if g.get_name() != "BeginSetup":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        if node.get_name() != "K2Node_GenericCreateObject_2":
            continue
        lines.append("=== node methods ===")
        for fn in sorted(dir(node)):
            if fn.startswith("_"):
                continue
            if any(k in fn.lower() for k in ("class", "object", "default", "spawn")):
                lines.append(f"  {fn}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            lines.append(f"PIN {pname}")
            for fn in sorted(dir(pin)):
                if fn.startswith("_"):
                    continue
                if any(k in fn.lower() for k in ("default", "object", "class")):
                    lines.append(f"  pin.{fn}")

OUT.write_text("\n".join(lines))
