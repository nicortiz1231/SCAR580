# Handoff: Remote enemy reload animation

**Date:** 2026-07-19  
**Project:** SCAR-580 (UE 5.8)  
**Status:** Exact FP reload via hidden pose-driver + upper-body bone copy (deployed).

---

## Current approach

`Anim_Arms_*_Reload` is **SK_Mannequin** (same skeleton as `SKM_Manny`). Playing it on standing `ABP_Manny` UpperBody looks wrong because of AnimBP context, not skeleton mismatch.

**Exact local path on remotes:**

1. Hidden `SCAR_ReloadPoseDriver`: `SKM_Manny` + `ABP_FP_ArmsProcedural`
2. Play exact kit `Anim_Arms_*_Reload` on **DefaultSlot** (same as local HandsSlot)
3. Each tick (`TG_PostUpdateWork`) while `IsRemoteReloadVisualActive()`: **parent-relative** copy of clavicle→hands + ik_hand_* onto body's render CS buffer (runtime-safe; no editor-only API). Spine stays from ABP_Manny so arms attach to the standing torso.
4. Gun stays on `ik_hand_gun`; `Anim_Weapon_*_Reload` + sound still play
5. `ABP_Manny` stays primary (look/aim/loco alive); UpperBody hold paused during window

---

## Key files

| File | Role |
|------|------|
| `SCARAvatarWeaponSyncComponent.cpp` | Pose driver, DefaultSlot play, bone copy |
| `SCARARMultiplayerPlayerState.cpp` | Multicast: weapon anim, sound, reload window; stops UpperBody |

---

## Do not reintroduce

- TP additive bake as primary
- FP DefaultSlot directly on linked ArmsProcedural of standing Manny + `weapon_r`
- `ABP_Mirror` / full `ABP_MannyRetarget` swap
- Raw full-skeleton FlipEditableSpaceBases stamp
- Arms Fire on UpperBody
