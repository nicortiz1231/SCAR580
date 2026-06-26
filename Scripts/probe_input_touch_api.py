"""Probe InputTouch event wiring API."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_input_touch_api.log")
lines = []


def log(msg: str) -> None:
    lines.append(msg)
    unreal.log(msg)


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)

for fn in sorted(dir(editor)):
    if "touch" in fn.lower() or "event" in fn.lower() or "input" in fn.lower():
        log(f"editor.{fn}")

for node in editor.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    if "Touch" in title or "Input" in title and "Event" in title:
        log(f"EXISTING {node.get_name()} | {title} | {node.get_class().get_name()}")

for name in ("InputTouch", "ReceiveTouchInput", "Touch", "BeginInputTouch"):
    try:
        node = editor.find_event_node(name)
        log(f"find_event_node({name!r}) -> {node}")
    except Exception as exc:
        log(f"find_event_node({name!r}) ERR {exc}")

OUT.write_text("\n".join(lines))
