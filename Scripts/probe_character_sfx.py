"""Probe sound nodes and exec upstream in BP_FPCharacter."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_character_sfx.log")
CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"

SOUND_NAMES = ("PlaySoundAtLocation", "SpawnSoundAtLocation", "PlaySound2D", "SpawnSound2D")


def title(node) -> str:
    return str(node.get_node_title()).replace("\n", " | ")


def upstream_exec(node, depth=0, seen=None):
    if seen is None:
        seen = set()
    nid = id(node)
    if nid in seen or depth > 12:
        return []
    seen.add(nid)
    exec_in = node.find_input_pin("execute")
    if not exec_in:
        return [title(node)]
    ups = []
    for pin in unreal.BlueprintGraphPinLibrary.list_connected_pins(exec_in):
        owner = pin.get_owning_node()
        ups.extend(upstream_exec(owner, depth + 1, seen))
    if not ups:
        ups = [title(node)]
    return ups


lines = []
bp = unreal.load_asset(f"{CHAR_BP}.BP_FPCharacter")
for graph in unreal.BlueprintEditorLibrary.list_graphs(bp):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    for node in editor.list_all_nodes():
        t = title(node)
        if not any(n in t for n in SOUND_NAMES):
            continue
        chain = upstream_exec(node)
        lines.append(f"[{graph.get_name()}] {node.get_name()} | {t}")
        lines.append(f"  upstream: {' <- '.join(chain[:8])}")

OUT.write_text("\n".join(lines) + "\n")
