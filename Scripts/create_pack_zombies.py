"""Create SCAR pack-zombie assets from Horror Kit + imported ZombieAnimationPack.

Creates under /Game/SCAR580/Zombies/:
- BS_Walk_Speed_Pack  (Idle/Run from /Game/ZombieAnimationPack/...)
- ABP_Enemy_Pack
- anim_Attack_A_Montage_Pack
- BP_Enemy_ZombiePack
"""

from __future__ import annotations

from pathlib import Path

import unreal

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/create_pack_zombies.log")

DEST = "/Game/SCAR580/Zombies"
KIT_BS = "/Game/FirstPersonHorrorKit/Characters/Enemy/BS_Walk_Speed"
KIT_ABP = "/Game/FirstPersonHorrorKit/Characters/Enemy/ABP_Enemy"
KIT_BP = "/Game/FirstPersonHorrorKit/Blueprints/Enemy/BP_Enemy"
KIT_MONTAGE = "/Game/FirstPersonHorrorKit/Demo/ZombieAnimationPack/Animations/Mannequin_UE5/anim_Attack_A_Montage"
PACK_IDLE = "/Game/ZombieAnimationPack/Animations/Mannequin_UE5/anim_Idle_A"
PACK_RUN = "/Game/ZombieAnimationPack/Animations/Mannequin_UE5/anim_Run_A"
PACK_ATTACK = "/Game/ZombieAnimationPack/Animations/Mannequin_UE5/anim_Attack_A"

OUT_BS = f"{DEST}/BS_Walk_Speed_Pack"
OUT_ABP = f"{DEST}/ABP_Enemy_Pack"
OUT_MONTAGE = f"{DEST}/anim_Attack_A_Montage_Pack"
OUT_BP = f"{DEST}/BP_Enemy_ZombiePack"


def log(msg: str) -> None:
    prev = LOG.read_text(encoding="utf-8") if LOG.exists() else ""
    LOG.write_text(prev + msg + "\n", encoding="utf-8")
    unreal.log(f"[create_pack_zombies] {msg}")
    print(msg)


def ensure_dir(path: str) -> None:
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)
        log(f"Created dir {path}")


def dup(src: str, dst: str):
    if unreal.EditorAssetLibrary.does_asset_exist(dst):
        log(f"Exists {dst}")
        return unreal.EditorAssetLibrary.load_asset(dst)
    if not unreal.EditorAssetLibrary.does_asset_exist(src):
        raise RuntimeError(f"Missing source {src}")
    asset = unreal.EditorAssetLibrary.duplicate_asset(src, dst)
    if not asset:
        raise RuntimeError(f"Failed duplicate {src} -> {dst}")
    log(f"Duplicated {src} -> {dst}")
    return asset


def retarget_blend_space(bs_path: str) -> None:
    bs = unreal.EditorAssetLibrary.load_asset(bs_path)
    idle = unreal.EditorAssetLibrary.load_asset(PACK_IDLE)
    run = unreal.EditorAssetLibrary.load_asset(PACK_RUN)
    if not bs or not idle or not run:
        raise RuntimeError("Failed loading BS/idle/run")

    # Prefer AnimationLibrary / BlendSpace helpers when available.
    samples = None
    for prop in ("sample_data", "SampleData"):
        try:
            samples = bs.get_editor_property(prop)
            log(f"BS sample prop={prop} count={len(list(samples)) if samples is not None else None}")
            break
        except Exception as exc:
            log(f"BS get {prop}: {exc}")

    if samples is None:
        # Try AnimationBlendSpaceFactory / rebuild via clear+add
        log("No sample_data property — trying BlendSpace API helpers")
        for name in dir(unreal):
            if "BlendSpace" in name and ("Library" in name or "Editor" in name):
                log(f"  available {name}")
        raise RuntimeError("Cannot access blend space samples")

    sample_list = list(samples)
    log(f"Sample count={len(sample_list)}")
    for i, sample in enumerate(sample_list):
        try:
            anim = sample.get_editor_property("animation")
        except Exception:
            try:
                anim = sample.get_editor_property("Animation")
            except Exception as exc:
                log(f"sample[{i}] anim get fail: {exc}")
                continue
        try:
            val = sample.get_editor_property("sample_value")
        except Exception:
            try:
                val = sample.get_editor_property("SampleValue")
            except Exception:
                val = None
        log(f"sample[{i}] anim={anim} value={val}")

        # Replace by speed: low -> idle, high -> run. If only 2 samples, map min/max.
        new_anim = None
        if val is not None:
            # sample_value may be float or vector
            try:
                speed = float(val)
            except Exception:
                try:
                    speed = float(val.x)
                except Exception:
                    speed = i
            new_anim = idle if speed < 150.0 else run
        else:
            new_anim = idle if i == 0 else run

        try:
            sample.set_editor_property("animation", new_anim)
        except Exception:
            sample.set_editor_property("Animation", new_anim)
        sample_list[i] = sample

    try:
        bs.set_editor_property("sample_data", sample_list)
    except Exception:
        bs.set_editor_property("SampleData", sample_list)

    unreal.EditorAssetLibrary.save_asset(bs_path, only_if_is_dirty=False)
    log(f"Retargeted blend space samples -> pack idle/run")


def replace_soft_refs(package_path: str, old_asset: str, new_asset: str) -> None:
    """Rewrite soft object paths inside a duplicated package when possible."""
    # Method 1: AssetRenameManager / redirectors style API
    try:
        old_path = unreal.SoftObjectPath(f"{old_asset}.{old_asset.split('/')[-1]}")
        new_path = unreal.SoftObjectPath(f"{new_asset}.{new_asset.split('/')[-1]}")
        log(f"Soft path rewrite {old_path} -> {new_path} in {package_path}")
    except Exception as exc:
        log(f"SoftObjectPath build fail: {exc}")

    # Method 2: consolidate / replace references via EditorAssetLibrary
    try:
        # UE exposes replace_references on some builds via AssetTools
        at = unreal.AssetToolsHelpers.get_asset_tools()
        if hasattr(at, "rename_referencing_soft_object_paths"):
            packages = [unreal.load_package(package_path)]
            at.rename_referencing_soft_object_paths(
                packages,
                [f"{old_asset}.{old_asset.split('/')[-1]}"],
                [f"{new_asset}.{new_asset.split('/')[-1]}"],
            )
            log("rename_referencing_soft_object_paths OK")
            return
    except Exception as exc:
        log(f"rename_referencing_soft_object_paths: {exc}")

    # Method 3: string search in loaded asset references
    try:
        asset = unreal.EditorAssetLibrary.load_asset(package_path)
        # AnimationBlueprint: walk soft refs via AssetRegistry
        ar = unreal.AssetRegistryHelpers.get_asset_registry()
        deps = ar.get_dependencies(
            unreal.AssetRegistryHelpers.get_asset(asset).package_name
            if False
            else unreal.TopLevelAssetPath(),
            unreal.AssetRegistryDependencyOptions(),
        )
        log(f"deps probe skipped/complex")
    except Exception as exc:
        log(f"deps: {exc}")

    # Method 4: For AnimBP, use EditorAssetSubsystem.replace_references if present
    try:
        eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
        if hasattr(eas, "consolidate_assets"):
            log("EditorAssetSubsystem.consolidate_assets available")
    except Exception as exc:
        log(f"EAS: {exc}")


def retarget_montage(montage_path: str) -> None:
    montage = unreal.EditorAssetLibrary.load_asset(montage_path)
    attack = unreal.EditorAssetLibrary.load_asset(PACK_ATTACK)
    if not montage or not attack:
        raise RuntimeError("Missing montage or pack attack")

    # AnimMontage slot tracks / segments
    changed = False
    for prop in ("slot_anim_tracks", "SlotAnimTracks"):
        try:
            tracks = list(montage.get_editor_property(prop))
        except Exception:
            continue
        log(f"Montage tracks via {prop}: {len(tracks)}")
        for ti, track in enumerate(tracks):
            for ap in ("anim_track", "AnimTrack"):
                try:
                    anim_track = track.get_editor_property(ap)
                except Exception:
                    continue
                for sp in ("anim_segments", "AnimSegments"):
                    try:
                        segs = list(anim_track.get_editor_property(sp))
                    except Exception:
                        continue
                    for si, seg in enumerate(segs):
                        for aprop in ("anim_reference", "AnimReference"):
                            try:
                                old = seg.get_editor_property(aprop)
                                seg.set_editor_property(aprop, attack)
                                segs[si] = seg
                                changed = True
                                log(f"Segment[{ti}:{si}] {old} -> {attack}")
                            except Exception as exc:
                                log(f"seg set fail: {exc}")
                    try:
                        anim_track.set_editor_property(sp, segs)
                    except Exception:
                        pass
        try:
            montage.set_editor_property(prop, tracks)
        except Exception:
            pass

    if not changed:
        # Fallback: AnimMontageFactory recreate
        log("Could not rewrite montage segments — trying set skeleton+sequence helpers")
        for name in dir(montage):
            if "sequence" in name.lower() or "anim" in name.lower():
                if not name.startswith("_"):
                    log(f"  montage attr {name}")

    unreal.EditorAssetLibrary.save_asset(montage_path, only_if_is_dirty=False)
    log(f"Montage saved changed={changed}")


def set_bp_anim_and_montage(bp_path: str, abp_path: str, montage_path: str) -> None:
    bp = unreal.EditorAssetLibrary.load_asset(bp_path)
    abp = unreal.EditorAssetLibrary.load_asset(abp_path)
    montage = unreal.EditorAssetLibrary.load_asset(montage_path)
    if not bp or not abp:
        raise RuntimeError("Missing BP/ABP")

    # Generated anim class
    anim_class = None
    try:
        anim_class = abp.generated_class()
    except Exception:
        anim_class = unreal.load_class(None, f"{abp_path}.{abp_path.split('/')[-1]}_C")

    cdo = unreal.get_default_object(bp.generated_class())
    mesh = None
    try:
        mesh = cdo.get_editor_property("mesh")
    except Exception:
        pass
    if mesh is None:
        try:
            mesh = cdo.get_component_by_class(unreal.SkeletalMeshComponent)
        except Exception as exc:
            log(f"mesh get fail: {exc}")

    if mesh and anim_class:
        try:
            mesh.set_editor_property("anim_class", anim_class)
            log(f"Set mesh.anim_class={anim_class}")
        except Exception as exc:
            try:
                mesh.set_animation_mode(unreal.AnimationMode.ANIMATION_BLUEPRINT)
                mesh.set_anim_instance_class(anim_class)
                log(f"Set anim instance class via API: {exc} then OK")
            except Exception as exc2:
                log(f"Set anim class failed: {exc2}")

    # Patch Play Montage node default on EventGraph if possible
    try:
        eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
        editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)
        for node in list(editor.list_all_nodes()):
            try:
                title = str(node.get_node_title(unreal.NodeTitleType.FULL_TITLE))
            except Exception:
                title = node.get_class().get_name()
            if "Play Montage" not in title and "PlayMontage" not in title:
                continue
            # Find MontageToPlay pin / property
            for prop in ("montage_to_play", "MontageToPlay"):
                try:
                    node.set_editor_property(prop, montage)
                    log(f"Set {node.get_name()}.{prop}")
                    break
                except Exception:
                    pass
            # Pins
            try:
                pins = list(unreal.BlueprintEditorLibrary.list_all_pins(node))
            except Exception:
                pins = []
            for pin in pins:
                try:
                    pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                except Exception:
                    try:
                        pname = str(pin.get_name())
                    except Exception:
                        continue
                if pname.lower() in ("montagetoplay", "montage_to_play"):
                    try:
                        pin.default_object = montage
                        log(f"Pin default_object MontageToPlay set")
                    except Exception as exc:
                        try:
                            unreal.BlueprintGraphPinLibrary.set_pin_default_value(pin, montage.get_path_name())
                            log("set_pin_default_value OK")
                        except Exception as exc2:
                            log(f"pin set fail: {exc} / {exc2}")
    except Exception as exc:
        log(f"Montage node patch: {exc}")

    # CanAttack true
    try:
        cdo.set_editor_property("can_attack_", True)
    except Exception:
        pass

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(bp_path, only_if_is_dirty=False)
    log(f"Saved BP {bp_path}")


def rewrite_abp_blendspace_ref() -> None:
    """Force ABP_Enemy_Pack to use BS_Walk_Speed_Pack via soft-path rename in package."""
    # Load both and use AssetRegistry dependency replace
    try:
        # Duplicate already copied soft refs to kit BS. Use EditorAssetLibrary.rename with redirector? 
        # Instead: use unreal.PackageTools
        old_name = f"{KIT_BS}.{KIT_BS.split('/')[-1]}"
        new_name = f"{OUT_BS}.{OUT_BS.split('/')[-1]}"
        log(f"Attempting package soft ref rewrite {old_name} -> {new_name}")

        # UE5 AssetTools method used by Fix Up Redirectors
        at = unreal.AssetToolsHelpers.get_asset_tools()
        methods = [m for m in dir(at) if "soft" in m.lower() or "rename" in m.lower() or "redirect" in m.lower()]
        log(f"AssetTools soft/rename methods: {methods}")

        if hasattr(unreal, "AssetRenameManager"):
            log("AssetRenameManager present")

        # Brute force: export text? Not available.
        # Use AnimBlueprint compile after setting preview mesh and manually finding nodes via editor.
        abp = unreal.EditorAssetLibrary.load_asset(OUT_ABP)
        # Try AnimationBlueprintEditorLibrary
        for lib_name in ("AnimationBlueprintLibrary", "AnimBlueprintLibrary", "AnimationBlueprintEditorLibrary"):
            lib = getattr(unreal, lib_name, None)
            if lib:
                log(f"Found {lib_name}: {[x for x in dir(lib) if not x.startswith('_')][:40]}")
    except Exception as exc:
        log(f"rewrite_abp: {exc}")

    # Graph node approach via BlueprintGraphEditor on AnimGraph
    try:
        abp = unreal.EditorAssetLibrary.load_asset(OUT_ABP)
        graphs = []
        try:
            graphs = list(abp.function_graphs)
        except Exception:
            pass
        try:
            if hasattr(unreal, "AnimBlueprintLibrary"):
                graphs.extend(list(unreal.AnimBlueprintLibrary.get_animation_graphs(abp)))
        except Exception as exc:
            log(f"get_animation_graphs: {exc}")

        pack_bs = unreal.EditorAssetLibrary.load_asset(OUT_BS)
        for g in graphs:
            if not g:
                continue
            name = g.get_name()
            if "AnimGraph" not in name and name != "AnimGraph":
                continue
            log(f"Scanning graph {name}")
            try:
                nodes = list(g.nodes)
            except Exception:
                try:
                    nodes = list(g.get_editor_property("nodes"))
                except Exception:
                    nodes = []
            for n in nodes:
                cls = n.get_class().get_name()
                if "BlendSpace" not in cls and "Blendspace" not in cls:
                    continue
                log(f"  node {n.get_name()} {cls}")
                for prop in ("blend_space", "BlendSpace", "blend_space_asset", "BlendSpaceAsset"):
                    try:
                        old = n.get_editor_property(prop)
                        n.set_editor_property(prop, pack_bs)
                        log(f"  set {prop}: {old} -> {pack_bs}")
                    except Exception:
                        pass
                # Nested FAnimNode_BlendSpacePlayer
                try:
                    node_struct = n.get_editor_property("node")
                    for prop in ("blend_space", "BlendSpace"):
                        try:
                            old = node_struct.get_editor_property(prop)
                            node_struct.set_editor_property(prop, pack_bs)
                            log(f"  node.{prop}: {old} -> {pack_bs}")
                        except Exception:
                            pass
                except Exception as exc:
                    log(f"  nested node: {exc}")
        unreal.BlueprintEditorLibrary.compile_blueprint(abp)
        unreal.EditorAssetLibrary.save_asset(OUT_ABP, only_if_is_dirty=False)
        log("ABP compiled/saved after BS swap attempt")
    except Exception as exc:
        log(f"AnimGraph BS swap failed: {exc}")


def main() -> None:
    if LOG.exists():
        LOG.unlink()
    log("=== create pack zombies ===")
    ensure_dir(DEST)

    dup(KIT_BS, OUT_BS)
    retarget_blend_space(OUT_BS)

    dup(KIT_ABP, OUT_ABP)
    rewrite_abp_blendspace_ref()

    dup(KIT_MONTAGE, OUT_MONTAGE)
    retarget_montage(OUT_MONTAGE)

    dup(KIT_BP, OUT_BP)
    set_bp_anim_and_montage(OUT_BP, OUT_ABP, OUT_MONTAGE)

    # Final saves
    for p in (OUT_BS, OUT_ABP, OUT_MONTAGE, OUT_BP):
        unreal.EditorAssetLibrary.save_asset(p, only_if_is_dirty=False)
        log(f"Final save {p} exists={unreal.EditorAssetLibrary.does_asset_exist(p)}")

    log("=== done ===")


main()
