"""Test blueprint node creation APIs for portrait layout."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_modding_node_api.log")
lines = []

editor_cls = unreal.BlueprintGraphEditor
for name in sorted(dir(editor_cls)):
    if any(k in name.lower() for k in ("branch", "self", "make", "node", "function")):
        lines.append(name)

wbp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Widgets/UI_WeaponModding.UI_WeaponModding")
eg = unreal.BlueprintEditorLibrary.find_event_graph(wbp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)

for fn in (
    "/Script/UMG.WidgetLayoutLibrary:GetViewportSize",
    "/Script/UMG.Widget:SetRenderScale",
    "/Script/UMG.Widget:SetRenderTransformPivot",
    "/Script/Engine.KismetMathLibrary:MakeVector2D",
):
    node = editor.add_call_function_node(fn)
    lines.append(f"add_call_function_node {fn} -> {node}")

for method in ("add_branch_node", "add_self_node"):
    if hasattr(editor, method):
        try:
            node = getattr(editor, method)()
            lines.append(f"{method}() -> {node}")
        except Exception as exc:
            lines.append(f"{method}() ERR {exc}")
    else:
        lines.append(f"{method} missing")

OUT.write_text("\n".join(lines))
