#include "SCARLocalFirstPersonArmsComponent.h"

#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/Controller.h"
#include "GameFramework/Pawn.h"

DEFINE_LOG_CATEGORY_STATIC(LogSCARLocalArms, Log, All);

USCARLocalFirstPersonArmsComponent::USCARLocalFirstPersonArmsComponent()
{
	// TG_PostUpdateWork runs after every other actor's default TG_PrePhysics
	// tick (where the character Blueprint's own aim/procedural-animation
	// logic writes CharacterMesh0's Pitch/Yaw each frame) has already
	// completed for this frame -- so our Roll write here always sticks.
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.TickGroup = TG_PostUpdateWork;
}

void USCARLocalFirstPersonArmsComponent::BeginPlay()
{
	Super::BeginPlay();

	if (APawn* Pawn = Cast<APawn>(GetOwner()))
	{
		TrySetup(Pawn);
	}
}

void USCARLocalFirstPersonArmsComponent::TrySetup(APawn* Pawn)
{
	if (!Pawn || !Pawn->IsLocallyControlled())
	{
		return;
	}

	if (!CachedBodyMesh)
	{
		CachedBodyMesh = FindMeshByExactName(Pawn, ThirdPersonMeshComponentName);
	}

	if (!CachedBodyMesh || bLegsHidden)
	{
		return;
	}

	for (const FName& BoneName : LegBonesToHide)
	{
		if (CachedBodyMesh->GetBoneIndex(BoneName) != INDEX_NONE)
		{
			CachedBodyMesh->HideBoneByName(BoneName, EPhysBodyOp::PBO_None);
		}
		else
		{
			UE_LOG(LogSCARLocalArms, Warning, TEXT("Leg bone '%s' not found on %s"), *BoneName.ToString(), *CachedBodyMesh->GetName());
		}
	}

	bLegsHidden = true;
	UE_LOG(LogSCARLocalArms, Log, TEXT("Hid local player's leg bones on %s"), *Pawn->GetName());
}

void USCARLocalFirstPersonArmsComponent::TickComponent(
	const float DeltaTime,
	const ELevelTick TickType,
	FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	APawn* Pawn = Cast<APawn>(GetOwner());
	if (!Pawn || !Pawn->IsLocallyControlled())
	{
		return;
	}

	if (!bLegsHidden)
	{
		TrySetup(Pawn);
	}

	ApplyRoll(Pawn);
}

void USCARLocalFirstPersonArmsComponent::ApplyRoll(const APawn* Pawn)
{
	const AController* PawnController = Pawn->GetController();
	if (!PawnController || !CachedBodyMesh)
	{
		return;
	}

	// Undo whatever Roll delta we injected last frame *before* reading the
	// mesh's current world rotation, so this never compounds across frames
	// regardless of whether the character Blueprint resets Roll to 0 on its
	// own each tick.
	if (!LastAppliedRollDeltaQuat.Equals(FQuat::Identity, 0.0001f))
	{
		const FQuat UndoneWorldQuat = LastAppliedRollDeltaQuat.Inverse() * CachedBodyMesh->GetComponentQuat();
		CachedBodyMesh->SetWorldRotation(UndoneWorldQuat);
		LastAppliedRollDeltaQuat = FQuat::Identity;
	}

	const FRotator ControlRot = PawnController->GetControlRotation();
	if (FMath::IsNearlyZero(ControlRot.Roll, 0.01f))
	{
		return;
	}

	// Isolate just the Roll contribution as a clean world-space quaternion
	// delta (see header comment for why this can't be done by writing the
	// FRotator.Roll field directly once Pitch is non-zero).
	FRotator ZeroRollControlRot = ControlRot;
	ZeroRollControlRot.Roll = 0.f;
	const FQuat RollDeltaQuat = ControlRot.Quaternion() * ZeroRollControlRot.Quaternion().Inverse();

	const FQuat NewWorldQuat = RollDeltaQuat * CachedBodyMesh->GetComponentQuat();
	CachedBodyMesh->SetWorldRotation(NewWorldQuat);
	LastAppliedRollDeltaQuat = RollDeltaQuat;
}

USkeletalMeshComponent* USCARLocalFirstPersonArmsComponent::FindMeshByExactName(
	const APawn* Pawn,
	const FName Name) const
{
	if (!Pawn)
	{
		return nullptr;
	}

	const FString TargetName = Name.ToString();
	TArray<USkeletalMeshComponent*> SkeletalMeshes;
	Pawn->GetComponents<USkeletalMeshComponent>(SkeletalMeshes);

	for (USkeletalMeshComponent* MeshComponent : SkeletalMeshes)
	{
		if (MeshComponent && MeshComponent->GetName() == TargetName)
		{
			return MeshComponent;
		}
	}

	return nullptr;
}
