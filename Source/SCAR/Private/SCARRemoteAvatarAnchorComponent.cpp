#include "SCARRemoteAvatarAnchorComponent.h"

#include "ARBlueprintLibrary.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerState.h"
#include "GameFramework/Pawn.h"
#include "HeadMountedDisplayFunctionLibrary.h"
#include "SCARARPoseSyncComponent.h"

USCARRemoteAvatarAnchorComponent::USCARRemoteAvatarAnchorComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	// After replication, character movement, and gameplay have settled the
	// pawn transform for this frame.
	PrimaryComponentTick.TickGroup = TG_LastDemotable;
}

USkeletalMeshComponent* USCARRemoteAvatarAnchorComponent::FindBodyMesh(APawn* Pawn) const
{
	if (!Pawn)
	{
		return nullptr;
	}

	const FString TargetName = BodyMeshComponentName.ToString();
	TArray<USkeletalMeshComponent*> Meshes;
	Pawn->GetComponents<USkeletalMeshComponent>(Meshes);
	for (USkeletalMeshComponent* Mesh : Meshes)
	{
		if (Mesh && Mesh->GetName() == TargetName)
		{
			return Mesh;
		}
	}

	return nullptr;
}

void USCARRemoteAvatarAnchorComponent::TickComponent(
	const float DeltaTime,
	const ELevelTick TickType,
	FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	const APlayerController* LocalPC = Cast<APlayerController>(GetOwner());
	UWorld* World = GetWorld();
	if (!World || !LocalPC || !LocalPC->IsLocalController())
	{
		return;
	}

	const FARSessionStatus SessionStatus = UARBlueprintLibrary::GetARSessionStatus();
	if (SessionStatus.Status != EARSessionStatus::Running)
	{
		RestoreAnchoredMeshes();
		return;
	}

	FRotator DeviceRotation;
	FVector DevicePosition;
	UHeadMountedDisplayFunctionLibrary::GetOrientationAndPosition(DeviceRotation, DevicePosition);
	const float DeviceRollDegrees = FRotator::NormalizeAxis(DeviceRotation.Roll);

	FVector ViewLocation;
	FRotator ViewRotation;
	LocalPC->GetPlayerViewPoint(ViewLocation, ViewRotation);
	ViewRotation.Roll = 0.f;

	const FQuat CameraQuat = ViewRotation.Quaternion();
	const FQuat CounterRollWorld =
		CameraQuat * FRotator(0.f, 0.f, -DeviceRollDegrees).Quaternion() * CameraQuat.Inverse();

	const APawn* LocalPawn = LocalPC->GetPawn();

	// During the join window our own pawn exists but is not possessed yet and
	// would look "remote"; never touch any pawn until possession completes.
	if (!LocalPawn)
	{
		return;
	}

	for (auto It = AnchoredMeshes.CreateIterator(); It; ++It)
	{
		if (!It.Key().IsValid() || !It.Value().Mesh.IsValid())
		{
			It.RemoveCurrent();
		}
	}

	for (TActorIterator<APawn> It(World); It; ++It)
	{
		APawn* Pawn = *It;
		if (!Pawn || Pawn == LocalPawn || Pawn->IsLocallyControlled())
		{
			continue;
		}

		if (!Pawn->GetPlayerState())
		{
			continue;
		}

		// Extra identity check: never treat a pawn owned by the local player
		// state as remote (covers possession races during join).
		if (LocalPC->PlayerState && Pawn->GetPlayerState() == LocalPC->PlayerState)
		{
			continue;
		}

		FMeshAnchorState* State = AnchoredMeshes.Find(Pawn);
		if (!State)
		{
			USkeletalMeshComponent* Mesh = FindBodyMesh(Pawn);
			if (!Mesh)
			{
				continue;
			}

			FMeshAnchorState NewState;
			NewState.Mesh = Mesh;
			NewState.DefaultRelative = Mesh->GetRelativeTransform();
			State = &AnchoredMeshes.Add(Pawn, NewState);
		}

		USkeletalMeshComponent* Mesh = State->Mesh.Get();
		if (!Mesh)
		{
			continue;
		}

		// Stateless: desired mesh world pose is derived from the replicated
		// pawn transform every frame; nothing we wrote last frame is read.
		FTransform PawnWorld = Pawn->GetActorTransform();

		// Prefer the replicated AR body yaw. Look pitch must stay on
		// RemoteViewPitch / ABP_Manny — tipping the whole mesh here made the
		// avatar rotate as a rigid stick and killed organic look.
		if (const USCARARPoseSyncComponent* PoseSync =
				Pawn->FindComponentByClass<USCARARPoseSyncComponent>())
		{
			if (PoseSync->HasValidARPose())
			{
				const FRotator Aim = PoseSync->GetCurrentARPose().Rotator();
				PawnWorld.SetRotation(FRotator(0.f, Aim.Yaw, 0.f).Quaternion());
			}
		}

		const FTransform MeshWorld = State->DefaultRelative * PawnWorld;

		const FVector AnchoredLocation =
			ViewLocation + CounterRollWorld.RotateVector(MeshWorld.GetLocation() - ViewLocation);
		const FQuat AnchoredRotation = (CounterRollWorld * MeshWorld.GetRotation()).GetNormalized();

		Mesh->SetWorldLocationAndRotation(AnchoredLocation, AnchoredRotation, false, nullptr, ETeleportType::TeleportPhysics);
	}
}

void USCARRemoteAvatarAnchorComponent::RestoreAnchoredMeshes()
{
	for (auto& Pair : AnchoredMeshes)
	{
		if (USkeletalMeshComponent* Mesh = Pair.Value.Mesh.Get())
		{
			Mesh->SetRelativeTransform(Pair.Value.DefaultRelative);
		}
	}
	AnchoredMeshes.Empty();
}
