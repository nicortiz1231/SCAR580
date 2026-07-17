#include "SCARARPoseSyncComponent.h"

#include "ARBlueprintLibrary.h"
#include "Engine/Engine.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/Controller.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "HeadMountedDisplayFunctionLibrary.h"
#include "Net/UnrealNetwork.h"
#include "SCARMultiplayerPresentationComponent.h"

USCARARPoseSyncComponent::USCARARPoseSyncComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	SetIsReplicatedByDefault(true);
}

void USCARARPoseSyncComponent::BeginPlay()
{
	Super::BeginPlay();

	if (AActor* Owner = GetOwner())
	{
		Owner->SetReplicateMovement(false);
	}

	if (ACharacter* Character = Cast<ACharacter>(GetOwner()))
	{
		if (UCharacterMovementComponent* Movement = Character->GetCharacterMovement())
		{
			Movement->SetMovementMode(MOVE_Flying);
			Movement->GravityScale = 0.f;
			Movement->bServerAcceptClientAuthoritativePosition = true;
		}
	}
}

void USCARARPoseSyncComponent::TickComponent(
	const float DeltaTime,
	const ELevelTick TickType,
	FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	AActor* Owner = GetOwner();
	if (!Owner)
	{
		return;
	}

	APawn* Pawn = Cast<APawn>(Owner);
	if (!Pawn)
	{
		return;
	}

	if (Pawn->IsLocallyControlled())
	{
		FTransform ARPose;
		if (SampleARPose(ARPose))
		{
			const FTransform BodyPose = BuildMultiplayerBodyPose(ARPose);
			CaptureSessionOriginIfNeeded(BodyPose);
			const FTransform RelativePose = LocalSessionOrigin.Inverse() * BodyPose;

			bHasValidARPose = true;
			ReplicatedARPose = RelativePose;

			if (bDriveOwnerFromARPose)
			{
				// Drive the hidden multiplayer body capsule with sanitized rotation
				// (no roll / no upside-down flip). Local FP arms are decoupled on
				// FirstPersonCamera via USCARLocalFirstPersonArmsComponent.
				ApplyPoseToOwner(BodyPose, false);
			}

			const double Now = Owner->GetWorld() ? Owner->GetWorld()->GetTimeSeconds() : 0.0;
			const double SendInterval = 1.0 / static_cast<double>(FMath::Max(PoseSendRateHz, 1.f));
			if (Now - LastPoseSendSeconds >= SendInterval)
			{
				LastPoseSendSeconds = Now;
				Server_UpdateARPose(RelativePose.GetLocation(), RelativePose.Rotator());
			}
		}
	}
	else
	{
		UpdateRemoteProxyPose(DeltaTime);
		SyncRemoteVisualizationRotation(Pawn);
	}
}

void USCARARPoseSyncComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(USCARARPoseSyncComponent, ReplicatedARPose);
}

FTransform USCARARPoseSyncComponent::GetCurrentARPose() const
{
	if (const APawn* Pawn = Cast<APawn>(GetOwner()))
	{
		if (Pawn->IsLocallyControlled())
		{
			return LocalSessionOrigin * ReplicatedARPose;
		}
	}

	return ComputeWorldPoseFromSessionRelative(ReplicatedARPose);
}

FTransform USCARARPoseSyncComponent::GetLocalViewerSessionOrigin(const UWorld* World)
{
	if (!World)
	{
		return FTransform::Identity;
	}

	for (FConstPlayerControllerIterator Iterator = World->GetPlayerControllerIterator(); Iterator; ++Iterator)
	{
		const APlayerController* PlayerController = Iterator->Get();
		if (!PlayerController || !PlayerController->IsLocalController())
		{
			continue;
		}

		const APawn* LocalPawn = PlayerController->GetPawn();
		if (!LocalPawn)
		{
			continue;
		}

		const USCARARPoseSyncComponent* PoseSync =
			LocalPawn->FindComponentByClass<USCARARPoseSyncComponent>();
		if (PoseSync && PoseSync->bHasLocalSessionOrigin)
		{
			return PoseSync->LocalSessionOrigin;
		}
	}

	return FTransform::Identity;
}

bool USCARARPoseSyncComponent::SampleARPose(FTransform& OutPose) const
{
	const UWorld* World = GetWorld();
	if (!World)
	{
		return false;
	}

	const FARSessionStatus SessionStatus = UARBlueprintLibrary::GetARSessionStatus();
	if (SessionStatus.Status == EARSessionStatus::Running)
	{
		FRotator DeviceRotation;
		FVector DevicePosition = FVector::ZeroVector;
		UHeadMountedDisplayFunctionLibrary::GetOrientationAndPosition(DeviceRotation, DevicePosition);

		const FTransform TrackingToWorld = UHeadMountedDisplayFunctionLibrary::GetTrackingToWorldTransform(
			const_cast<UWorld*>(World));
		const FTransform DevicePose(DeviceRotation, DevicePosition);
		const FTransform WorldDevicePose = TrackingToWorld * DevicePose;
		OutPose = WorldDevicePose;
		return true;
	}

	const APawn* Pawn = Cast<APawn>(GetOwner());
	const APlayerController* PC = Pawn ? Cast<APlayerController>(Pawn->GetController()) : nullptr;
	if (!PC)
	{
		return false;
	}

	FVector ViewLocation;
	FRotator ViewRotation;
	PC->GetPlayerViewPoint(ViewLocation, ViewRotation);
	OutPose = FTransform(ViewRotation, ViewLocation);
	return true;
}

void USCARARPoseSyncComponent::CaptureSessionOriginIfNeeded(const FTransform& CurrentPose)
{
	if (!bHasLocalSessionOrigin)
	{
		LocalSessionOrigin = CurrentPose;
		bHasLocalSessionOrigin = true;
	}
}

FTransform USCARARPoseSyncComponent::ComputeWorldPoseFromSessionRelative(const FTransform& RelativePose) const
{
	return GetLocalViewerSessionOrigin(GetWorld()) * RelativePose;
}

FRotator USCARARPoseSyncComponent::SanitizeMultiplayerBodyRotation(const FRotator& DeviceRotation) const
{
	FRotator BodyRotation = DeviceRotation;
	BodyRotation.Roll = 0.f;
	BodyRotation.Pitch = FMath::Clamp(
		BodyRotation.Pitch,
		-MaxMultiplayerBodyPitchDegrees,
		MaxMultiplayerBodyPitchDegrees);
	return BodyRotation.GetNormalized();
}

FTransform USCARARPoseSyncComponent::BuildMultiplayerBodyPose(const FTransform& DeviceWorldPose) const
{
	const FVector BodyLocation = DeviceWorldPose.TransformPosition(BodyOffsetFromCamera);
	const FRotator BodyRotation = SanitizeMultiplayerBodyRotation(DeviceWorldPose.Rotator());
	return FTransform(BodyRotation, BodyLocation);
}

void USCARARPoseSyncComponent::SyncRemoteVisualizationRotation(APawn* Pawn)
{
	if (!Pawn || Pawn->IsLocallyControlled() || !bHasValidARPose)
	{
		return;
	}

	if (AController* Controller = Pawn->GetController())
	{
		Controller->SetControlRotation(GetCurrentARPose().Rotator());
	}
}

void USCARARPoseSyncComponent::ApplyPoseToOwner(const FTransform& Pose, const bool bTeleport)
{
	AActor* Owner = GetOwner();
	if (!Owner)
	{
		return;
	}

	Owner->SetActorLocationAndRotation(
		Pose.GetLocation(),
		Pose.Rotator(),
		false,
		nullptr,
		bTeleport ? ETeleportType::TeleportPhysics : ETeleportType::None);

	// ControlRotation for the local camera + camera-attached FP arms is owned by
	// ASCARARMultiplayerPlayerController::PlayerTick (smoothed AR device pose).
	// Writing it here as well raced that path and reintroduced jitter on the
	// view the local player sees.
}

void USCARARPoseSyncComponent::UpdateProxyInterpolation(const float DeltaTime)
{
	AActor* Owner = GetOwner();
	if (!Owner || !bHasValidARPose)
	{
		return;
	}

	const FVector CurrentLocation = Owner->GetActorLocation();
	const FQuat CurrentRotation = Owner->GetActorQuat();
	const FVector TargetLocation = ProxyTargetPose.GetLocation();
	const FQuat TargetRotation = ProxyTargetPose.GetRotation();

	const float Alpha = FMath::Clamp(DeltaTime * ProxyInterpolationSpeed, 0.f, 1.f);
	const FVector NewLocation = FMath::Lerp(CurrentLocation, TargetLocation, Alpha);
	const FQuat NewRotation = FQuat::Slerp(CurrentRotation, TargetRotation, Alpha).GetNormalized();

	Owner->SetActorLocationAndRotation(NewLocation, NewRotation.Rotator(), false, nullptr, ETeleportType::None);
}

void USCARARPoseSyncComponent::UpdateRemoteProxyPose(const float DeltaTime)
{
	if (const AActor* Owner = GetOwner())
	{
		if (const USCARMultiplayerPresentationComponent* Presentation =
			Owner->FindComponentByClass<USCARMultiplayerPresentationComponent>())
		{
			if (Presentation->IsUsingViewPlacementForLocalViewer())
			{
				return;
			}
		}
	}

	if (!bHasValidARPose)
	{
		return;
	}

	ProxyTargetPose = ComputeWorldPoseFromSessionRelative(ReplicatedARPose);

	if (!bHasSnappedRemotePose)
	{
		ApplyPoseToOwner(ProxyTargetPose, true);
		bHasSnappedRemotePose = true;
		return;
	}

	UpdateProxyInterpolation(DeltaTime);
}

void USCARARPoseSyncComponent::OnRep_ReplicatedARPose()
{
	bHasValidARPose = true;
	bHasSnappedRemotePose = false;
}

void USCARARPoseSyncComponent::Server_UpdateARPose_Implementation(
	const FVector_NetQuantize Location,
	const FRotator Rotation)
{
	ReplicatedARPose = FTransform(Rotation, FVector(Location));
	bHasValidARPose = true;
}
