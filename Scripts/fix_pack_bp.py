"""Set BP_Enemy_ZombiePack Play Montage pin to pack montage; verify wiring."""

from __future__ import annotations

from pathlib import Path

import unreal

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_pack_bp.log")
OUT_BP = "/Game/SCAR580/Zombies/BP_Enemy_ZombiePack"
OUT_ABP = "/Game/SCAR580/Zombies/ABP_Enemy_Pack"
OUT_MONTAGE = "/Game/SCAR580/Zombies/anim_Attack_A_Montage_Pack"
OUT_BS = "/Game/SCAR580/Zombies/BS_Walk_Speed_Pack"


def log(msg: str) -> None:
    prev = LOG.read_text(encoding="utf-8") if LOG.exists() else ""
    LOG.write_text(prev + msg + "\n", encoding="utf-8")
    print(msg)
    unreal.log(f"[fix_pack_bp] {msg}")


def main():
    if LOG.exists():
        LOG.unlink()
    log("=== start ===")

    bp = unreal.EditorAssetLibrary.load_asset(OUT_BP)
    montage = unreal.EditorAssetLibrary.load_asset(OUT_MONTAGE)
    abp = unreal.EditorAssetLibrary.load_asset(OUT_ABP)
    anim_class = abp.generated_class()

    cdo = unreal.get_default_object(bp.generated_class())
    mesh = cdo.get_editor_property("mesh")
    log(f"mesh.anim_class before={mesh.get_editor_property('anim_class') if mesh else None}")
    if mesh and anim_class:
        mesh.set_editor_property("anim_class", anim_class)
        log(f"mesh.anim_class set={anim_class.get_path_name()}")

    # CanAttack
    for prop in ("can_attack_", "CanAttack_", "can_attack", "b_can_attack"):
        try:
            old = cdo.get_editor_property(prop)
            cdo.set_editor_property(prop, True)
            log(f"set {prop} {old} -> True")
        except Exception:
            pass

    eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)
    for node in list(editor.list_all_nodes()):
        try:
            title = str(node.get_node_title(unreal.NodeTitleType.LIST_VIEW))
        except Exception:
            title = node.get_class().get_name()
        cls = node.get_class().get_name()
        if "montage" not in title.lower() and "Montage" not in cls:
            continue
        log(f"NODE {title} | {cls}")
        for pin in list(unreal.BlueprintEditorLibrary.list_all_pins(node)):
            pname = str(pin.get_name())
            dval = getattr(pin, "default_value", None)
            log(f"  pin {pname} default={dval}")
            if "montage" not in pname.lower():
                continue
            # Preferred: BlueprintGraphEditor helpers
            methods = [m for m in dir(editor) if "default" in m.lower() or "pin" in m.lower()]
            log(f"  editor methods sample={[m for m in methods if not m.startswith('_')][:30]}")
            ok = False
            # try set via pin default_value property on the pin UObject
            for setter in (
                lambda: pin.set_editor_property("default_value", montage.get_path_name()),
                lambda: pin.set_editor_property("DefaultValue", montage.get_path_name()),
                lambda: setattr(pin, "default_value", montage.get_path_name()),
            ):
                try:
                    setter()
                    ok = True
                    log(f"  setter ok now={getattr(pin, 'default_value', None)}")
                    break
                except Exception as exc:
                    log(f"  setter fail: {exc}")

            # Try call_method patterns on editor
            for name in ("set_pin_default_value", "SetPinDefaultValue"):
                if hasattr(editor, name):
                    try:
                        getattr(editor, name)(pin, montage.get_path_name())
                        ok = True
                        log(f"  {name} ok")
                    except Exception as exc:
                        log(f"  {name}: {exc}")

            # Object pin: use make_link / default object via unreal.EdGraphPin
            try:
                # Some builds: pin.default_object
                pin.set_editor_property("default_object", montage)
                ok = True
                log("  default_object set")
            except Exception as exc:
                log(f"  default_object: {exc}")

            log(f"  final ok={ok} default={getattr(pin, 'default_value', None)}")

    # Also search for PlayMontage in functions (Atack)
    try:
        for fn in list(bp.function_graphs or []):
            log(f"function_graph {fn.get_name() if fn else None}")
    except Exception as exc:
        log(f"function_graphs: {exc}")

    # Walk all graphs for montage nodes
    for gname in ("EventGraph", "Atack", "Attack", "UserConstructionScript"):
        try:
            g = unreal.BlueprintEditorLibrary.find_graph(bp, gname)
        except Exception:
            g = None
        if not g:
            continue
        try:
            ged = unreal.BlueprintGraphEditor.get_graph_editor(g)
            for node in list(ged.list_all_nodes()):
                cls = node.get_class().get_name()
                if "Montage" not in cls and "montage" not in str(node.get_node_title(unreal.NodeTitleType.LIST_VIEW)).lower():
                    continue
                log(f"GRAPH {gname}: {cls}")
                for pin in list(unreal.BlueprintEditorLibrary.list_all_pins(node)):
                    if "montage" in str(pin.get_name()).lower():
                        try:
                            pin.set_editor_property("default_value", montage.get_path_name())
                            log(f"  set {pin.get_name()} -> {montage.get_path_name()}")
                        except Exception as exc:
                            log(f"  pin set: {exc}")
                        log(f"  now={getattr(pin, 'default_value', None)}")
        except Exception as exc:
            log(f"graph {gname}: {exc}")

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(OUT_BP, only_if_is_dirty=False)

    # Verify ABP BS still pack
    abp = unreal.EditorAssetLibrary.load_asset(OUT_ABP)
    graph = unreal.BlueprintEditorLibrary.find_graph(abp, "AnimGraph")
    editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    for n in list(editor.list_all_nodes()):
        if n.get_class().get_name() == "AnimGraphNode_BlendSpacePlayer":
            bs = n.get_editor_property("node").get_editor_property("blend_space")
            log(f"VERIFY ABP BS={bs.get_path_name() if bs else None}")

    # Verify montage sequence
    mont = unreal.EditorAssetLibrary.load_asset(OUT_MONTAGE)
    track = list(mont.get_editor_property("slot_anim_tracks"))[0]
    seg = list(track.get_editor_property("anim_track").get_editor_property("anim_segments"))[0]
    anim = seg.get_editor_property("anim_reference")
    log(f"VERIFY montage anim={anim.get_path_name() if anim else None}")

    # Verify mesh anim class after compile
    bp = unreal.EditorAssetLibrary.load_asset(OUT_BP)
    cdo = unreal.get_default_object(bp.generated_class())
    mesh = cdo.get_editor_property("mesh")
    log(f"VERIFY mesh.anim_class={mesh.get_editor_property('anim_class') if mesh else None}")

    log("=== done ===")


main()
