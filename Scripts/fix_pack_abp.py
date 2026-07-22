"""Swap ABP_Enemy_Pack AnimGraph BlendSpace to BS_Walk_Speed_Pack; fix BP montage pin."""

from __future__ import annotations

from pathlib import Path

import unreal

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_pack_abp.log")
OUT_ABP = "/Game/SCAR580/Zombies/ABP_Enemy_Pack"
OUT_BS = "/Game/SCAR580/Zombies/BS_Walk_Speed_Pack"
OUT_BP = "/Game/SCAR580/Zombies/BP_Enemy_ZombiePack"
OUT_MONTAGE = "/Game/SCAR580/Zombies/anim_Attack_A_Montage_Pack"


def log(msg: str) -> None:
    prev = LOG.read_text(encoding="utf-8") if LOG.exists() else ""
    LOG.write_text(prev + msg + "\n", encoding="utf-8")
    unreal.log(f"[fix_pack_abp] {msg}")
    print(msg)


def dump_props(obj, prefix=""):
    # Try common editor properties
    for prop in (
        "node", "Node", "blend_space", "BlendSpace", "blend_space_asset",
        "BlendSpaceAsset", "blendspace", "sample_data",
    ):
        try:
            val = obj.get_editor_property(prop)
            log(f"{prefix}{prop}={val}")
            return prop, val
        except Exception:
            pass
    return None, None


def fix_abp() -> None:
    abp = unreal.EditorAssetLibrary.load_asset(OUT_ABP)
    pack_bs = unreal.EditorAssetLibrary.load_asset(OUT_BS)
    graph = unreal.BlueprintEditorLibrary.find_graph(abp, "AnimGraph")
    log(f"AnimGraph={graph}")
    nodes = list(graph.nodes) if graph else []
    log(f"node count={len(nodes)}")
    swapped = 0
    for n in nodes:
        cls = n.get_class().get_name()
        name = n.get_name()
        log(f"NODE {name} {cls}")
        # Dump all editor-accessible props that look relevant
        for attr in dir(n):
            if attr.startswith("_"):
                continue
            low = attr.lower()
            if any(k in low for k in ("blend", "space", "anim", "node", "asset")):
                try:
                    val = getattr(n, attr)
                    if callable(val):
                        continue
                    log(f"  attr {attr}={val}")
                except Exception:
                    pass
        # get_editor_property sweep for blend space
        for prop in ("node", "Node", "blend_space", "BlendSpace", "blend_space_asset", "BlendSpaceAsset"):
            try:
                val = n.get_editor_property(prop)
                log(f"  editor {prop} type={type(val)} val={val}")
                if prop.lower() == "node" and val is not None:
                    for bp in ("blend_space", "BlendSpace", "BlendSpaceAsset", "blend_space_asset", "X", "x"):
                        try:
                            old = val.get_editor_property(bp)
                            log(f"    node.{bp}={old}")
                            if "blend" in bp.lower() or "space" in bp.lower():
                                val.set_editor_property(bp, pack_bs)
                                # write back
                                n.set_editor_property(prop, val)
                                swapped += 1
                                log(f"    SWAPPED node.{bp} -> {pack_bs.get_path_name()}")
                        except Exception as exc:
                            log(f"    node.{bp}: {exc}")
                if "blend" in prop.lower() or prop.endswith("Space") or prop.endswith("Asset"):
                    n.set_editor_property(prop, pack_bs)
                    swapped += 1
                    log(f"  SWAPPED {prop}")
            except Exception as exc:
                log(f"  {prop}: {exc}")

        # Try struct copy via unreal.AnimGraphNode_BlendSpacePlayer if class matches
        if "BlendSpace" in cls:
            try:
                # Some versions expose BlendSpace on the node directly as UProperty
                n.set_editor_property("BlendSpace", pack_bs)
                swapped += 1
                log("  direct BlendSpace set")
            except Exception as exc:
                log(f"  direct BlendSpace: {exc}")

    log(f"swapped_ops={swapped}")
    unreal.BlueprintEditorLibrary.compile_blueprint(abp)
    unreal.EditorAssetLibrary.save_loaded_asset(abp)
    unreal.EditorAssetLibrary.save_asset(OUT_ABP, only_if_is_dirty=False)

    refs_kit = unreal.EditorAssetLibrary.find_package_referencers_for_asset(
        "/Game/FirstPersonHorrorKit/Characters/Enemy/BS_Walk_Speed", False
    )
    refs_pack = unreal.EditorAssetLibrary.find_package_referencers_for_asset(OUT_BS, False)
    log(f"kit BS refs: {list(refs_kit) if refs_kit else None}")
    log(f"pack BS refs: {list(refs_pack) if refs_pack else None}")


def fix_bp_montage() -> None:
    bp = unreal.EditorAssetLibrary.load_asset(OUT_BP)
    montage = unreal.EditorAssetLibrary.load_asset(OUT_MONTAGE)
    eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)
    nodes = list(editor.list_all_nodes())
    log(f"BP nodes={len(nodes)}")
    for node in nodes:
        try:
            title = str(node.get_node_title(unreal.NodeTitleType.LIST_VIEW))
        except Exception:
            title = node.get_class().get_name()
        if "montage" not in title.lower() and "Montage" not in node.get_class().get_name():
            continue
        log(f"HIT {title} {node.get_class().get_name()}")
        pins = list(unreal.BlueprintEditorLibrary.list_all_pins(node))
        for pin in pins:
            pname = str(pin.get_name())
            log(f"  pin={pname} default={getattr(pin, 'default_value', None)}")
            if "montage" in pname.lower():
                # Try editor helpers
                ok = False
                try:
                    # K2Node_PlayMontage has MontageToPlay as object pin
                    pin.make_link_to  # existence
                except Exception:
                    pass
                for meth_name in ("set_pin_default_value", "SetPinDefaultValue", "set_default_value"):
                    meth = getattr(editor, meth_name, None) or getattr(pin, meth_name, None)
                    if not meth:
                        continue
                    try:
                        meth(pin, montage.get_path_name()) if meth.__self__ is editor else meth(montage.get_path_name())
                        ok = True
                        log(f"  {meth_name} OK")
                        break
                    except Exception as exc:
                        try:
                            meth(montage.get_path_name())
                            ok = True
                            log(f"  {meth_name} OK2")
                            break
                        except Exception as exc2:
                            log(f"  {meth_name}: {exc} / {exc2}")
                # Last resort: write default_value string
                try:
                    pin.set_editor_property("default_value", montage.get_path_name())
                    ok = True
                    log("  default_value editor prop OK")
                except Exception as exc:
                    log(f"  default_value: {exc}")
                try:
                    # Some pins use DefaultObject
                    pin.set_editor_property("default_object", montage)
                    ok = True
                    log("  default_object OK")
                except Exception as exc:
                    log(f"  default_object: {exc}")
                log(f"  result ok={ok} now={getattr(pin, 'default_value', None)}")

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(OUT_BP, only_if_is_dirty=False)
    log("BP saved")


def main():
    if LOG.exists():
        LOG.unlink()
    log("=== start ===")
    fix_abp()
    fix_bp_montage()
    log("=== done ===")


main()
