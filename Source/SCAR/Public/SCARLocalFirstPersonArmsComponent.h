#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SCARLocalFirstPersonArmsComponent.generated.h"

class USkeletalMeshComponent;

/**
 * Restores the classic "arms glued to the camera" FPS feel (rotate your
 * phone, the arms/weapon visually "lean" with it) and hides the local
 * player's own legs when looking down, WITHOUT introducing a second mesh.
 *
 * Why not a second mesh: two earlier attempts at this rendered a dedicated
 * arms-only mesh (SKM_Camera, the same asset USCARMultiplayerPresentationComponent
 * uses as a hidden pose driver for mirroring opponents) either camera-attached
 * or capsule-attached with SetOnlyOwnerSee, and both rendered nothing at all
 * on-device even after fixing a confirmed empty-material-slot bug on that
 * asset. The capsule-relative offset that component uses
 * (PoseDriverRelativeLocation = (15, 0, 65)) is calibrated for a third-person
 * silhouette as seen by *other* players, not for how it lines up with the
 * local FirstPersonCamera up close -- that mismatch (or SetOnlyOwnerSee simply
 * not doing what's expected in this AR pass-through pipeline) is the most
 * likely reason nothing showed up, but there wasn't a way to visually verify
 * either theory without another slow on-device round trip.
 *
 * So instead, this sticks to the one mesh that is *already proven* to render
 * correctly with proper weapon-hand IK from the local FirstPersonCamera --
 * CharacterMesh0 (BP_FPCharacter's own body mesh) -- and does two small,
 * low-risk things to it:
 *
 * 1. HideBoneByName on "thigh_l"/"thigh_r" once at setup. Verified via the UE5.8
 *    Skeleton editor subsystem that on SKM_Manny's skeleton, both thighs are
 *    direct children of "pelvis" (siblings of "spine_01", not ancestors of
 *    it), and hiding a bone cascades to its children only -- so this removes
 *    the entire leg chain (calf/foot/ball + twist bones) while leaving the
 *    pelvis, spine, arms, hands, and head fully visible. There is no bone
 *    partition on this single continuous mesh that can hide the torso too
 *    while keeping the arms, since the arms are downstream of the spine
 *    bones in the rig (clavicle_l/r's parent is spine_05) -- doing that would
 *    need a real arms-only asset, which is exactly what the two failed
 *    attempts above were trying to use.
 *
 * 2. Every tick (in TG_PostUpdateWork, i.e. after the character Blueprint's
 *    own TG_PrePhysics tick has set this frame's Pitch/Yaw), makes
 *    CharacterMesh0 share the camera's Roll -- via a proper quaternion
 *    delta, NOT by overwriting the FRotator.Roll field directly.
 *
 *    The passthrough video itself always visually tilts as you physically
 *    tilt the phone (that's just the camera sensor -- nothing in Unreal
 *    controls it). So "arms locked to the camera preview" really means the
 *    3D-rendered arms should show *zero* apparent rotation on screen, ever;
 *    the "leaning" illusion comes entirely from the passthrough tilting
 *    behind an arms overlay that never itself rotates on screen. Since the
 *    virtual camera's Roll already tracks the device (ASCARARMultiplayer
 *    PlayerController::PlayerTick drives ControlRotation from the live,
 *    smoothed AR device pose, and FirstPersonCamera/SpringArm follow it via
 *    bUsePawnControlRotation), the fix is to make CharacterMesh0 share that
 *    exact same Roll contribution, so camera and mesh always differ by zero
 *    relative Roll -- i.e. on screen, the arms don't rotate at all.
 *
 *    A first version of this literally did `MeshRotation.Roll = TargetRoll`
 *    on CharacterMesh0's relative rotation each tick. That is NOT the same
 *    thing as "share the camera's Roll" once the mesh also has non-zero
 *    Pitch (from the game's own aim-offset) -- FRotator's Roll/Pitch/Yaw
 *    don't commute, so overwriting just the Roll field of an already-pitched
 *    rotation produces a wildly different, contorted final 3D orientation,
 *    not a clean tilt (this is what caused the arms to spin wildly instead
 *    of staying put when tilting the phone). The fix here instead computes
 *    RollDeltaQuat = Quat(ControlRotation) * Quat(ControlRotation with Roll
 *    zeroed out).Inverse() -- a clean world-space quaternion isolating just
 *    the Roll contribution -- and left-multiplies that onto the mesh's
 *    current world rotation (whatever Pitch/Yaw the Blueprint set this
 *    frame, untouched). LastAppliedRollDeltaQuat is undone before each
 *    reapplication so this never compounds across frames even if the
 *    character Blueprint doesn't reset Roll to 0 on its own.
 *
 * Bone-hiding affects CharacterMesh0 for every viewer (there's no per-viewer
 * bone visibility), so right now opponents will also see this player's legs
 * hidden -- that's a known, accepted trade-off versus risking another totally
 * invisible arms mesh; showing opponents a full mannequin again is a
 * follow-up, not a blocker for getting arms + tilt back.
 *
 * Only affects the locally-controlled pawn on this client -- opponents'
 * pawns aren't touched, since ASCARARMultiplayerPlayerController only
 * attaches this to its own local pawn.
 */
UCLASS(ClassGroup = (SCAR), meta = (BlueprintSpawnableComponent))
class SCAR_API USCARLocalFirstPersonArmsComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	USCARLocalFirstPersonArmsComponent();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|FirstPerson")
	FName ThirdPersonMeshComponentName = TEXT("CharacterMesh0");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|FirstPerson")
	TArray<FName> LegBonesToHide = {TEXT("thigh_l"), TEXT("thigh_r")};

protected:
	virtual void BeginPlay() override;
	virtual void TickComponent(
		float DeltaTime,
		ELevelTick TickType,
		FActorComponentTickFunction* ThisTickFunction) override;

private:
	void TrySetup(APawn* Pawn);
	void ApplyRoll(const APawn* Pawn);
	USkeletalMeshComponent* FindMeshByExactName(const APawn* Pawn, FName Name) const;

	UPROPERTY()
	TObjectPtr<USkeletalMeshComponent> CachedBodyMesh;

	bool bLegsHidden = false;

	FQuat LastAppliedRollDeltaQuat = FQuat::Identity;
};
