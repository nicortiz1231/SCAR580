"""Probe ABP_Enemy and ABP_Enemy_Pack EventGraph for Set Velocity / BP Enemy cast."""

from __future__ import annotations

from pathlib import Path

import unreal

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_abp_velocity.log")
KIT_ABP = "/Game/FirstPersonHorrorKit/Characters/Enemy/ABP_Enemy"
PACK_ABP = "/Game/SCAR580/Zombies/ABP_Enemy_Pack"


def log(msg: str) -> None:
    prev = LOG.read_text(encoding="utf-8") if LOG.exists() else ""
    LOG.write_text(prev + msg + "\n", encoding="utf-8")
    print(msg)
    unreal.log(f"[probe_abp_vel] {msg}")


def dump_abp(path: str) -> None:
    log(f"=== {path} ===")
    abp = unreal.EditorAssetLibrary.load_asset(path)
    # Variables
    try:
        for v in list(abp.new_variables or []):
            log(f"  var {v.variable_name} type={v.var_type}")
    except Exception as exc:
        log(f"  new_variables: {exc}")
    try:
        vars2 = unreal.BlueprintEditorLibrary.get_blueprint_variable_list(abp)
        log(f"  get_blueprint_variable_list={vars2}")
    except Exception as exc:
        log(f"  get_blueprint_variable_list: {exc}")

    eg = unreal.BlueprintEditorLibrary.find_graph(abp, "EventGraph")
    editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)
    for n in list(editor.list_all_nodes()):
        title = str(n.get_node_title(unreal.NodeTitleType.FULL_TITLE))
        cls = n.get_class().get_name()
        log(f"  NODE {cls} | {title}")
        if any(k in title.lower() or k in cls.lower() for k in ("velocity", "bp enemy", "cast", "pawn", "movement", "event tick", "try get")):
            for pin in list(unreal.BlueprintEditorLibrary.list_all_pins(n)):
                pname = str(pin.get_name())
                dval = getattr(pin, "default_value", None)
                log(f"    pin {pname} def={dval}")


def main():
    if LOG.exists():
        LOG.unlink()
    dump_abp(KIT_ABP)
    dump_abp(PACK_ABP)
    log("=== done ===")


main()
