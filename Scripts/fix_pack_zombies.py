"""Verify + fix pack zombie asset wiring (BS samples, ABP blend space, BP montage)."""

from __future__ import annotations

from pathlib import Path

import unreal

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_pack_zombies.log")

DEST = "/Game/SCAR580/Zombies"
KIT_BS = "/Game/FirstPersonHorrorKit/Characters/Enemy/BS_Walk_Speed"
OUT_BS = f"{DEST}/BS_Walk_Speed_Pack"
OUT_ABP = f"{DEST}/ABP_Enemy_Pack"
OUT_MONTAGE = f"{DEST}/anim_Attack_A_Montage_Pack"
OUT_BP = f"{DEST}/BP_Enemy_ZombiePack"
PACK_IDLE = "/Game/ZombieAnimationPack/Animations/Mannequin_UE5/anim_Idle_A"
PACK_RUN = "/Game/ZombieAnimationPack/Animations/Mannequin_UE5/anim_Run_A"
PACK_ATTACK = "/Game/ZombieAnimationPack/Animations/Mannequin_UE5/anim_Attack_A"


def log(msg: str) -> None:
    prev = LOG.read_text(encoding="utf-8") if LOG.exists() else ""
    LOG.write_text(prev + msg + "\n", encoding="utf-8")
    unreal.log(f"[fix_pack_zombies] {msg}")
    print(msg)


def speed_of(sample) -> float:
    try:
        val = sample.get_editor_property("sample_value")
    except Exception:
        val = sample.get_editor_property("SampleValue")
    try:
        return float(val)
    except Exception:
        try:
            return float(val.x)
        except Exception:
            return 0.0


def fix_blend_space() -> None:
    bs = unreal.EditorAssetLibrary.load_asset(OUT_BS)
    idle = unreal.EditorAssetLibrary.load_asset(PACK_IDLE)
    run = unreal.EditorAssetLibrary.load_asset(PACK_RUN)
    samples = list(bs.get_editor_property("sample_data"))
    for i, sample in enumerate(samples):
        anim = sample.get_editor_property("animation")
        spd = speed_of(sample)
        new_anim = idle if spd < 150.0 else run
        sample.set_editor_property("animation", new_anim)
        samples[i] = sample
        log(f"BS sample[{i}] speed={spd} {anim.get_path_name() if anim else None} -> {new_anim.get_path_name()}")
    bs.set_editor_property("sample_data", samples)
    unreal.EditorAssetLibrary.save_asset(OUT_BS, only_if_is_dirty=False)

    # Re-read
    bs = unreal.EditorAssetLibrary.load_asset(OUT_BS)
    for i, sample in enumerate(list(bs.get_editor_property("sample_data"))):
        anim = sample.get_editor_property("animation")
        log(f"VERIFY BS[{i}] = {anim.get_path_name() if anim else None}")


def fix_abp_blendspace() -> None:
    old = f"{KIT_BS}.{KIT_BS.split('/')[-1]}"
    new = f"{OUT_BS}.{OUT_BS.split('/')[-1]}"
    at = unreal.AssetToolsHelpers.get_asset_tools()

    # Find soft refs in ABP package
    try:
        refs = at.find_soft_references_to_object(unreal.load_asset(KIT_BS))
        log(f"Soft refs to kit BS count={len(list(refs)) if refs else 0}")
        for r in list(refs or [])[:20]:
            log(f"  softref {r}")
    except Exception as exc:
        log(f"find_soft_references_to_object: {exc}")

    # Rename soft object paths inside ABP package
    try:
        pkg = unreal.load_package(OUT_ABP)
        at.rename_referencing_soft_object_paths([pkg], [old], [new])
        log(f"rename_referencing_soft_object_paths {old} -> {new}")
    except Exception as exc:
        log(f"rename_referencing_soft_object_paths failed: {exc}")

    # Also walk AnimGraph nodes
    abp = unreal.EditorAssetLibrary.load_asset(OUT_ABP)
    pack_bs = unreal.EditorAssetLibrary.load_asset(OUT_BS)
    graphs = []
    try:
        graphs.extend(list(abp.ubergraph_pages or []))
    except Exception:
        pass
    try:
        graphs.extend(list(abp.function_graphs or []))
    except Exception:
        pass
    # Anim blueprints store anim graphs separately
    for attr in ("animation_graphs", "AnimationGraphs", "anim_blueprint_extension_data"):
        try:
            val = abp.get_editor_property(attr)
            log(f"ABP.{attr}={val}")
        except Exception as exc:
            log(f"ABP.{attr}: {exc}")

    # Use AssetRegistry dependencies
    try:
        ar = unreal.AssetRegistryHelpers.get_asset_registry()
        deps = ar.get_dependencies(
            OUT_ABP,
            unreal.AssetRegistry.DependencyOptions() if False else None,
        )
    except Exception as exc:
        log(f"deps attempt: {exc}")

    try:
        # Package name without asset
        options = unreal.AssetRegistryDependencyOptions()
        options.include_soft_package_references = True
        options.include_hard_package_references = True
        dep_names = ar.get_dependencies(OUT_ABP, options)
        log(f"ABP deps: {list(dep_names) if dep_names else None}")
    except Exception as exc:
        log(f"get_dependencies: {exc}")

    # Brute: serialize search via EditorAssetLibrary.find_package_referencers_for_asset
    try:
        refs = unreal.EditorAssetLibrary.find_package_referencers_for_asset(KIT_BS, False)
        log(f"Referencers of kit BS: {list(refs) if refs else None}")
        pack_refs = unreal.EditorAssetLibrary.find_package_referencers_for_asset(OUT_BS, False)
        log(f"Referencers of pack BS: {list(pack_refs) if pack_refs else None}")
    except Exception as exc:
        log(f"find_package_referencers: {exc}")

    # Try setting on AnimGraph nodes via BlueprintEditorLibrary get all nodes
    try:
        # Load as AnimationBlueprint
        anim_graphs = []
        if hasattr(unreal, "AnimationBlueprintLibrary"):
            pass
        # EdGraph on AnimBlueprint: get_editor_property('function_graphs') includes AnimGraph sometimes
        for g in list(getattr(abp, "function_graphs", []) or []):
            log(f"function_graph {g.get_name() if g else None}")
        # Also try ubergraph
        for gname in ("AnimGraph", "EventGraph"):
            try:
                g = unreal.BlueprintEditorLibrary.find_graph(abp, gname)
                log(f"find_graph {gname}={g}")
            except Exception as exc:
                log(f"find_graph {gname}: {exc}")

        # Direct nodes access on all graphs from blueprint
        try:
            all_graphs = unreal.BlueprintEditorLibrary.get_all_graphs(abp)
            log(f"get_all_graphs count={len(list(all_graphs)) if all_graphs else 0}")
            for g in list(all_graphs or []):
                gname = g.get_name()
                nodes = list(g.nodes) if g else []
                log(f"graph {gname} nodes={len(nodes)}")
                for n in nodes:
                    cls = n.get_class().get_name()
                    if "Blend" in cls or "blend" in cls.lower():
                        log(f"  BLEND NODE {n.get_name()} {cls}")
                        for prop in dir(n):
                            if "blend" in prop.lower() or "space" in prop.lower():
                                if not prop.startswith("_"):
                                    try:
                                        log(f"    {prop}={getattr(n, prop, None)}")
                                    except Exception:
                                        pass
                        # FAnimNode inside
                        for prop in ("node", "Node", "blend_space", "BlendSpace"):
                            try:
                                val = n.get_editor_property(prop)
                                log(f"    editor {prop}={val}")
                                if prop.lower() in ("node",):
                                    for bp in ("blend_space", "BlendSpace", "blendspace", "BlendSpaceAsset"):
                                        try:
                                            oldv = val.get_editor_property(bp)
                                            val.set_editor_property(bp, pack_bs)
                                            log(f"    swapped node.{bp}: {oldv} -> {pack_bs}")
                                        except Exception as e2:
                                            log(f"    node.{bp}: {e2}")
                                if "blend" in prop.lower():
                                    n.set_editor_property(prop, pack_bs)
                                    log(f"    set {prop}")
                            except Exception as e1:
                                log(f"    {prop}: {e1}")
        except Exception as exc:
            log(f"get_all_graphs walk: {exc}")
    except Exception as exc:
        log(f"ABP graph walk: {exc}")

    unreal.BlueprintEditorLibrary.compile_blueprint(abp)
    unreal.EditorAssetLibrary.save_asset(OUT_ABP, only_if_is_dirty=False)
    log("ABP saved")

    # Re-check referencers
    try:
        refs = unreal.EditorAssetLibrary.find_package_referencers_for_asset(KIT_BS, False)
        pack_refs = unreal.EditorAssetLibrary.find_package_referencers_for_asset(OUT_BS, False)
        log(f"AFTER kit BS refs: {list(refs) if refs else None}")
        log(f"AFTER pack BS refs: {list(pack_refs) if pack_refs else None}")
    except Exception as exc:
        log(f"after refs: {exc}")


def fix_bp_montage() -> None:
    bp = unreal.EditorAssetLibrary.load_asset(OUT_BP)
    montage = unreal.EditorAssetLibrary.load_asset(OUT_MONTAGE)
    abp = unreal.EditorAssetLibrary.load_asset(OUT_ABP)
    anim_class = abp.generated_class()

    cdo = unreal.get_default_object(bp.generated_class())
    mesh = cdo.get_editor_property("mesh")
    if mesh and anim_class:
        mesh.set_editor_property("anim_class", anim_class)
        log(f"mesh.anim_class={anim_class.get_path_name()}")

    eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)
    for node in list(editor.list_all_nodes()):
        title = str(node.get_node_title(unreal.NodeTitleType.FULL_TITLE))
        cls = node.get_class().get_name()
        if "Montage" not in title and "Montage" not in cls and "Play Montage" not in title:
            continue
        log(f"Montage-ish node: {title} | {cls} | {node.get_name()}")
        pins = list(unreal.BlueprintEditorLibrary.list_all_pins(node))
        for pin in pins:
            try:
                pname = str(pin.get_name())
            except Exception:
                pname = "?"
            try:
                ptype = str(pin.pin_type)
            except Exception:
                ptype = "?"
            try:
                dval = pin.default_value
            except Exception:
                dval = None
            log(f"  pin {pname} type={ptype} default={dval}")
            if pname.lower() in ("montagetoplay", "montage_to_play"):
                # Try multiple pin set APIs
                for attempt in (
                    lambda: setattr(pin, "default_value", montage.get_path_name()),
                    lambda: pin.set_editor_property("default_value", montage.get_path_name()),
                    lambda: pin.set_editor_property("DefaultValue", montage.get_path_name()),
                    lambda: unreal.BlueprintEditorLibrary.set_pin_default_value(pin, montage.get_path_name()),
                    lambda: editor.set_pin_default_value(pin, montage.get_path_name()),
                    lambda: editor.call_method("SetPinDefaultValue", (pin, montage.get_path_name())),
                ):
                    try:
                        attempt()
                        log(f"  set pin OK -> {montage.get_path_name()}")
                        break
                    except Exception as exc:
                        log(f"  attempt fail: {exc}")

                # Also try node property
                for prop in ("montage_to_play", "MontageToPlay"):
                    try:
                        node.set_editor_property(prop, montage)
                        log(f"  node.{prop} set")
                    except Exception as exc:
                        log(f"  node.{prop}: {exc}")

    # Also look for any soft object property on CDO that stores montage
    for prop_name in dir(cdo):
        if "montage" in prop_name.lower() or "attack" in prop_name.lower():
            if prop_name.startswith("_"):
                continue
            try:
                log(f"CDO attr {prop_name}={getattr(cdo, prop_name, None)}")
            except Exception:
                pass

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(OUT_BP, only_if_is_dirty=False)
    log("BP saved")


def verify_montage() -> None:
    montage = unreal.EditorAssetLibrary.load_asset(OUT_MONTAGE)
    tracks = list(montage.get_editor_property("slot_anim_tracks"))
    for ti, track in enumerate(tracks):
        anim_track = track.get_editor_property("anim_track")
        segs = list(anim_track.get_editor_property("anim_segments"))
        for si, seg in enumerate(segs):
            anim = seg.get_editor_property("anim_reference")
            log(f"VERIFY montage seg[{ti}:{si}]={anim.get_path_name() if anim else None}")


def main() -> None:
    if LOG.exists():
        LOG.unlink()
    log("=== fix pack zombies ===")
    fix_blend_space()
    fix_abp_blendspace()
    fix_bp_montage()
    verify_montage()
    log("=== done ===")


main()
