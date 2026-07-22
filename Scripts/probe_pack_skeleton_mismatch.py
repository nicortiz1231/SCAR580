"""Probe kit enemy mesh skeleton vs pack / HorrorKit Demo anim skeletons."""
from __future__ import annotations

import unreal

ASSETS = {
    "kit_bp": "/Game/FirstPersonHorrorKit/Blueprints/Enemy/BP_Enemy",
    "kit_abp": "/Game/FirstPersonHorrorKit/Characters/Enemy/ABP_Enemy",
    "kit_bs": "/Game/FirstPersonHorrorKit/Characters/Enemy/BS_Walk_Speed",
    "kit_mesh_candidate": "/Game/FirstPersonHorrorKit/Characters/Enemy",  # dir probe
    "demo_idle": "/Game/FirstPersonHorrorKit/Demo/ZombieAnimationPack/Animations/Mannequin_UE5/anim_Idle_A",
    "demo_walk": "/Game/FirstPersonHorrorKit/Demo/ZombieAnimationPack/Animations/Mannequin_UE5/anim_Walk_A",
    "demo_crawl": "/Game/FirstPersonHorrorKit/Demo/ZombieAnimationPack/Animations/Mannequin_UE5/anim_Belly_Crawling_A",
    "demo_run": "/Game/FirstPersonHorrorKit/Demo/ZombieAnimationPack/Animations/Mannequin_UE5/anim_Run_A",
    "demo_attack_mtg": "/Game/FirstPersonHorrorKit/Demo/ZombieAnimationPack/Animations/Mannequin_UE5/anim_Attack_A_Montage",
    "import_idle": "/Game/ZombieAnimationPack/Animations/Mannequin_UE5/anim_Idle_A",
    "import_walk": "/Game/ZombieAnimationPack/Animations/Mannequin_UE5/anim_Walk_A",
    "pack_skel": "/Game/ZombieAnimationPack/Demo/EpicContent/Mannequin_UE5/Meshes/SKEL_Mannequin",
    "pack_mesh": "/Game/ZombieAnimationPack/Demo/EpicContent/Mannequin_UE5/Meshes/SK_Manny_Simple",
    "abp_pack": "/Game/SCAR580/Zombies/ABP_Enemy_Pack",
    "bs_pack": "/Game/SCAR580/Zombies/BS_Walk_Speed_Pack",
}


def skel_of(obj):
    if obj is None:
        return None
    for attr in ("skeleton", "Skeleton", "target_skeleton", "TargetSkeleton"):
        try:
            s = obj.get_editor_property(attr) if hasattr(obj, "get_editor_property") else getattr(obj, attr, None)
            if s:
                return s
        except Exception:
            pass
    # AnimSequence / Montage
    try:
        return obj.get_editor_property("skeleton")
    except Exception:
        pass
    return None


def path_of(obj):
    if obj is None:
        return None
    try:
        return obj.get_path_name()
    except Exception:
        return str(obj)


def main():
    print("=== ASSET EXISTENCE ===")
    for k, p in ASSETS.items():
        if k == "kit_mesh_candidate":
            continue
        print(f"{k}: exists={unreal.EditorAssetLibrary.does_asset_exist(p)}")

    print("\n=== ANIM SKELETONS ===")
    for k in ("demo_idle", "demo_walk", "demo_crawl", "demo_run", "demo_attack_mtg", "import_idle", "import_walk"):
        a = unreal.EditorAssetLibrary.load_asset(ASSETS[k])
        print(f"{k}: type={type(a).__name__ if a else None} skel={path_of(skel_of(a))}")

    print("\n=== PACK MESH / SKEL ===")
    for k in ("pack_skel", "pack_mesh"):
        a = unreal.EditorAssetLibrary.load_asset(ASSETS[k])
        print(f"{k}: type={type(a).__name__ if a else None} path={path_of(a)} skel={path_of(skel_of(a))}")
        if a and isinstance(a, unreal.SkeletalMesh):
            try:
                print(f"  skeletal_mesh.skeleton={path_of(a.get_editor_property('skeleton'))}")
            except Exception as e:
                print(f"  skeleton err: {e}")

    print("\n=== KIT BP_ENEMY MESH / ANIMCLASS ===")
    bp = unreal.EditorAssetLibrary.load_asset(ASSETS["kit_bp"])
    if bp:
        try:
            cdo = unreal.get_default_object(bp.generated_class())
        except Exception:
            cdo = None
            try:
                gc = bp.get_editor_property("generated_class")
                cdo = unreal.get_default_object(gc) if gc else None
            except Exception as e:
                print(f"cdo err: {e}")
        if cdo:
            mesh = cdo.get_component_by_class(unreal.SkeletalMeshComponent)
            if mesh:
                sm = mesh.skeletal_mesh
                print(f"mesh_comp={mesh.get_name()}")
                print(f"skeletal_mesh={path_of(sm)}")
                print(f"mesh_skel={path_of(skel_of(sm)) if sm else None}")
                try:
                    print(f"anim_class={path_of(mesh.get_anim_class())}")
                except Exception as e:
                    print(f"anim_class err: {e}")
                try:
                    print(f"anim_mode={mesh.get_editor_property('animation_mode')}")
                except Exception as e:
                    print(f"anim_mode err: {e}")
                try:
                    print(f"rel_loc={mesh.get_relative_location()}")
                except Exception:
                    pass
            else:
                print("no skeletal mesh component on CDO")

    print("\n=== KIT ABP / BS SKELETON ===")
    for k in ("kit_abp", "kit_bs", "abp_pack", "bs_pack"):
        a = unreal.EditorAssetLibrary.load_asset(ASSETS[k])
        print(f"{k}: type={type(a).__name__ if a else None} skel={path_of(skel_of(a))}")
        if a and hasattr(a, "get_editor_property"):
            for prop in ("target_skeleton", "preview_skeletal_mesh", "PreviewSkeletalMesh"):
                try:
                    v = a.get_editor_property(prop)
                    if v:
                        print(f"  {prop}={path_of(v)}")
                except Exception:
                    pass

    # Compatibility check via AnimationLibrary if available
    print("\n=== COMPAT CHECK (demo_walk vs kit mesh) ===")
    try:
        bp = unreal.EditorAssetLibrary.load_asset(ASSETS["kit_bp"])
        cdo = unreal.get_default_object(bp.generated_class())
        mesh = cdo.get_component_by_class(unreal.SkeletalMeshComponent)
        sm = mesh.skeletal_mesh
        walk = unreal.EditorAssetLibrary.load_asset(ASSETS["demo_walk"])
        kit_skel = skel_of(sm)
        walk_skel = skel_of(walk)
        print(f"same_object={kit_skel == walk_skel}")
        print(f"kit_skel={path_of(kit_skel)}")
        print(f"walk_skel={path_of(walk_skel)}")
        pack_mesh = unreal.EditorAssetLibrary.load_asset(ASSETS["pack_mesh"])
        pack_skel = skel_of(pack_mesh)
        print(f"pack_mesh_skel={path_of(pack_skel)}")
        print(f"walk_matches_pack_mesh={walk_skel == pack_skel}")
        import_walk = unreal.EditorAssetLibrary.load_asset(ASSETS["import_walk"])
        print(f"import_walk_skel={path_of(skel_of(import_walk))}")
        print(f"demo_vs_import_same={skel_of(walk) == skel_of(import_walk)}")
    except Exception as e:
        print(f"compat err: {e}")

    # Find any enemy mesh under HorrorKit
    print("\n=== HORRORKIT ENEMY MESH ASSETS ===")
    assets = unreal.EditorAssetLibrary.list_assets("/Game/FirstPersonHorrorKit/Characters/Enemy", recursive=True)
    for a in assets:
        if "SK" in a or "Mesh" in a or "Manny" in a or "Zombie" in a:
            print(a)


if __name__ == "__main__":
    main()
