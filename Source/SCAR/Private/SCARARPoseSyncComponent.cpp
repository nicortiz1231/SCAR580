#include "SCARARPoseSyncComponent.h"

#include "ARBlueprintLibrary.h"
#include "Components/CapsuleComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/Controller.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "HeadMountedDisplayFunctionLibrary.h"
#include "Net/UnrealNetwork.h"
#include "SCARMultiplayerPresentationComponent.h"
#include "SCARSharedARGround.h"
#include "SCARAvatarGrounding.h"
#include "SCARMultiplayerPawnSetup.h"

namespace SCARARPoseSync
{
	bool TryGetLocalViewerBodyPose(const UWorld* World, FTransform& OutBodyPose)
	{
		if (!World)
		{
			return false;
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
			if (!PoseSync || !PoseSync->HasValidARPose())
			{
				continue;
			}

			OutBodyPose = PoseSync->GetCurrentARPose();
			return true;
		}

		return false;
	}
}

bool USCARARPoseSyncComponent::IsARSessionActive()
{
	return UARBlueprintLibrary::GetARSessionStatus().Status == EARSessionStatus::Running;
}

FRotator USCARARPoseSyncComponent::MakeUprightYawRotation(const FRotator& Rotation)
{
	return FRotator(0.f, Rotation.Yaw, 0.f);
}

USCARARPoseSyncComponent::USCARARPoseSyncComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	SetIsReplicatedByDefault(true);
}

void USCARARPoseSyncComponent::BeginPlay()
{
	Super::BeginPlay();

	SCARMultiplayerPawnSetup::EnsureMultiplayerFloor(GetWorld());

	if (AActor* Owner = GetOwner())
	{
		Owner->SetReplicateMovement(false);
	}

	if (ACharacter* Character = Cast<ACharacter>(GetOwner()))
	{
		if (UCharacterMovementComponent* Movement = Character->GetCharacterMovement())
		{
			// Use walking mode so WASD + ABP_Manny locomotion work in editor,
			// and so the character stays grounded when we snap to AR ground.
			Movement->SetMovementMode(MOVE_Walking);
			Movement->GravityScale = 1.f;
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
		EnsureWalkingMovement(Pawn);

		const bool bDesktopWorldPose = !IsARSessionActive();

		if (bDesktopWorldPose)
		{
			SCARMultiplayerPawnSetup::EnsureMultiplayerFloor(GetWorld());
		}

		FTransform ARPose;
		if (SampleARPose(ARPose))
		{
			const FTransform BodyPose = IsARSessionActive()
				? BuildMultiplayerBodyPose(ARPose)
				: FTransform(MakeUprightYawRotation(ARPose.Rotator()), ARPose.GetLocation());

			CaptureSessionOriginIfNeeded(BodyPose);
			ReplicatedARPose = MakeWorldPoseForReplication(BodyPose, bDesktopWorldPose);

			bHasValidARPose = true;

			const double Now = Owner->GetWorld() ? Owner->GetWorld()->GetTimeSeconds() : 0.0;
			const double SendInterval = 1.0 / static_cast<double>(FMath::Max(PoseSendRateHz, 1.f));
			if (Now - LastPoseSendSeconds >= SendInterval)
			{
				LastPoseSendSeconds = Now;
				Server_UpdateARPose(ReplicatedARPose.GetLocation(), ReplicatedARPose.Rotator());
			}
		}

		if (bDesktopWorldPose)
		{
			// Editor WASD: let CharacterMovement walk on the floor — don't teleport Z every frame.
			if (ACharacter* Character = Cast<ACharacter>(Pawn))
			{
				if (UCharacterMovementComponent* Movement = Character->GetCharacterMovement())
				{
					if (!Movement->IsMovingOnGround())
					{
						const FVector Loc = Pawn->GetActorLocation();
						const FVector Snapped = SnapLocationToSharedGround(Loc);
						if (!FMath::IsNearlyEqual(Loc.Z, Snapped.Z, 2.f))
						{
							Pawn->SetActorLocation(FVector(Loc.X, Loc.Y, Snapped.Z));
						}
						Movement->SetMovementMode(MOVE_Walking);
					}
				}
			}
		}
		else
		{
			if (ACharacter* Character = Cast<ACharacter>(Pawn))
			{
				if (UCharacterMovementComponent* Movement = Character->GetCharacterMovement())
				{
					// AR avatars are pose-driven — gravity + per-frame Z snaps cause visible bobbing.
					Movement->GravityScale = 0.f;
					Movement->Velocity.Z = 0.f;
				}
			}

			const FVector CurrentLocation = Pawn->GetActorLocation();
			const FVector SnappedLocation = SnapLocationToSharedGround(CurrentLocation);
			if (!FMath::IsNearlyEqual(CurrentLocation.Z, SnappedLocation.Z, 2.f))
			{
				Pawn->SetActorLocation(
					FVector(CurrentLocation.X, CurrentLocation.Y, SnappedLocation.Z),
					false,
					nullptr,
					ETeleportType::TeleportPhysics);
			}
		}
	}
	else
	{
		EnsureWalkingMovement(Pawn);
		UpdateRemoteProxyPose(DeltaTime);
		SyncRemoteVisualizationRotation(Pawn);
		SyncRemoteLocomotionVelocity(Pawn, DeltaTime);
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
			if (IsARSessionActive())
			{
				return LocalSessionOrigin * ReplicatedARPose;
			}

			return ReplicatedARPose;
		}
	}

	return ComputeWorldPoseFromSessionRelative(ReplicatedARPose);
}

FTransform USCARARPoseSyncComponent::MakeWorldPoseForReplication(
	const FTransform& BodyPose,
	const bool bDesktopWorldPose) const
{
	if (bDesktopWorldPose)
	{
		FVector WorldLocation = BodyPose.GetLocation();
		WorldLocation.Z = SnapLocationToSharedGround(WorldLocation).Z;
		return FTransform(MakeUprightYawRotation(BodyPose.Rotator()), WorldLocation);
	}

	return LocalSessionOrigin.Inverse() * BodyPose;
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
		if (PoseSync && PoseSync->HasLocalSessionOrigin())
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

	const APawn* Pawn = Cast<APawn>(GetOwner());
	const APlayerController* PC = Pawn ? Cast<APlayerController>(Pawn->GetController()) : nullptr;

	const FARSessionStatus SessionStatus = UARBlueprintLibrary::GetARSessionStatus();
	if (SessionStatus.Status == EARSessionStatus::Running)
	{
		FRotator DeviceRotation;
		FVector DevicePosition = FVector::ZeroVector;
		UHeadMountedDisplayFunctionLibrary::GetOrientationAndPosition(DeviceRotation, DevicePosition);

		const FTransform TrackingToWorld = UHeadMountedDisplayFunctionLibrary::GetTrackingToWorldTransform(
			const_cast<UWorld*>(World));
		const FTransform DevicePose(DeviceRotation, DevicePosition);
		FTransform WorldDevicePose = TrackingToWorld * DevicePose;

		// World tracking moves the render camera when you walk; use view location for XYZ.
		if (PC)
		{
			FVector ViewLocation;
			FRotator ViewRotation;
			PC->GetPlayerViewPoint(ViewLocation, ViewRotation);
			WorldDevicePose.SetLocation(ViewLocation);
		}

		OutPose = WorldDevicePose;
		return true;
	}

	if (!PC)
	{
		return false;
	}

	// Editor / non-AR desktop testing: replicate actual pawn movement (WASD).
	if (Pawn)
	{
		OutPose = FTransform(MakeUprightYawRotation(Pawn->GetControlRotation()), Pawn->GetActorLocation());
		return true;
	}

	return false;
}

void USCARARPoseSyncComponent::CaptureSessionOriginIfNeeded(const FTransform& CurrentPose)
{
	if (!bHasLocalSessionOrigin)
	{
		LocalSessionOrigin = CurrentPose;
		bHasLocalSessionOrigin = true;
		SpawnSharedGroundIfNeeded(CurrentPose);
	}
}

void USCARARPoseSyncComponent::SpawnSharedGroundIfNeeded(const FTransform& BodyPose)
{
	if (!bSpawnSharedGround || SpawnedSharedGround.IsValid())
	{
		return;
	}

	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	const float CapsuleHalfHeight = GetOwnerCapsuleHalfHeight();
	const FVector OriginLocation = BodyPose.GetLocation();

	float SurfaceZ = OriginLocation.Z - CapsuleHalfHeight;
	float TracedGroundZ = 0.f;
	if (SCARAvatarGrounding::TraceGroundWorldZ(World, OriginLocation, SurfaceZ, TracedGroundZ, GetOwner()))
	{
		SurfaceZ = TracedGroundZ;
	}

	if (ASCARSharedARGround* Existing = ASCARSharedARGround::FindInWorld(World))
	{
		Existing->PlaceAt(OriginLocation, SurfaceZ);
		SpawnedSharedGround = Existing;
		return;
	}

	FActorSpawnParameters SpawnParams;
	SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	SpawnParams.Owner = GetOwner();

	ASCARSharedARGround* Ground = World->SpawnActor<ASCARSharedARGround>(
		ASCARSharedARGround::StaticClass(),
		FVector::ZeroVector,
		FRotator::ZeroRotator,
		SpawnParams);
	if (!Ground)
	{
		return;
	}

	Ground->PlaceAt(OriginLocation, SurfaceZ);
	SpawnedSharedGround = Ground;
}

FTransform USCARARPoseSyncComponent::ComputeWorldPoseFromSessionRelative(const FTransform& RelativePose) const
{
	// Editor / desktop PIE: ReplicatedARPose is already world-space WASD movement.
	if (!IsARSessionActive())
	{
		FVector WorldLocation = RelativePose.GetLocation();
		WorldLocation.Z = SnapLocationToSharedGround(WorldLocation).Z;

		FTransform WorldPose;
		WorldPose.SetLocation(WorldLocation);
		WorldPose.SetRotation(MakeUprightYawRotation(RelativePose.Rotator()).Quaternion());
		return WorldPose;
	}

	const UWorld* World = GetWorld();
	const FTransform Origin = GetLocalViewerSessionOrigin(World);

	// World-lock using the captured session origin only. Do NOT re-project through the
	// live viewer body/camera — that rotates the opponent when you look around.
	FVector WorldLocation = Origin.TransformPosition(RelativePose.GetLocation());
	WorldLocation.Z = SnapLocationToSharedGround(WorldLocation).Z;

	FTransform WorldPose;
	WorldPose.SetLocation(WorldLocation);
	WorldPose.SetRotation((Origin.GetRotation() * RelativePose.GetRotation()).GetNormalized());
	return WorldPose;
}

float USCARARPoseSyncComponent::GetOwnerCapsuleHalfHeight() const
{
	if (const ACharacter* Character = Cast<ACharacter>(GetOwner()))
	{
		if (const UCapsuleComponent* Capsule = Character->GetCapsuleComponent())
		{
			return Capsule->GetScaledCapsuleHalfHeight();
		}
	}

	return 88.f;
}

FVector USCARARPoseSyncComponent::SnapLocationToSharedGround(const FVector& Location) const
{
	const float CapsuleHalfHeight = GetOwnerCapsuleHalfHeight();

	float GroundZ = 0.f;
	if (SCARAvatarGrounding::TraceGroundWorldZ(GetWorld(), Location, Location.Z - CapsuleHalfHeight, GroundZ, GetOwner()))
	{
		FVector Snapped = Location;
		Snapped.Z = GroundZ + CapsuleHalfHeight;
		return Snapped;
	}

	return Location;
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
	FVector BodyLocation = DeviceWorldPose.TransformPosition(BodyOffsetFromCamera);
	BodyLocation.Z = SnapLocationToSharedGround(BodyLocation).Z;

	const FRotator BodyRotation = SanitizeMultiplayerBodyRotation(DeviceWorldPose.Rotator());
	return FTransform(BodyRotation, BodyLocation);
}

void USCARARPoseSyncComponent::EnsureWalkingMovement(APawn* Pawn)
{
	if (ACharacter* Character = Cast<ACharacter>(Pawn))
	{
		if (UCharacterMovementComponent* Movement = Character->GetCharacterMovement())
		{
			Movement->GravityScale = 1.f;
			if (Movement->MovementMode == MOVE_Flying || Movement->MovementMode == MOVE_None)
			{
				Movement->SetMovementMode(MOVE_Walking);
			}
		}
	}
}

void USCARARPoseSyncComponent::SyncRemoteLocomotionVelocity(APawn* Pawn, const float DeltaTime)
{
	if (!Pawn || Pawn->IsLocallyControlled())
	{
		return;
	}

	ACharacter* Character = Cast<ACharacter>(Pawn);
	if (!Character)
	{
		return;
	}

	UCharacterMovementComponent* Movement = Character->GetCharacterMovement();
	if (!Movement)
	{
		return;
	}

	// ABP_Manny reads CharacterMovement velocity for walk/run blends.
	const float SafeDt = FMath::Max(DeltaTime, KINDA_SMALL_NUMBER);
	const FVector Delta = (Pawn->GetActorLocation() - LastRemoteLocationForVelocity) / SafeDt;
	LastRemoteLocationForVelocity = Pawn->GetActorLocation();
	Movement->Velocity = FVector(Delta.X, Delta.Y, 0.f);
}

void USCARARPoseSyncComponent::SyncRemoteVisualizationRotation(APawn* Pawn)
{
	if (!Pawn || Pawn->IsLocallyControlled() || !bHasValidARPose)
	{
		return;
	}

	const FRotator AimRotation = SanitizeMultiplayerBodyRotation(GetCurrentARPose().Rotator());

	Pawn->SetRemoteViewPitch(AimRotation.Pitch);

	if (AController* Controller = Pawn->GetController())
	{
		Controller->SetControlRotation(AimRotation);
	}

	const FRotator ActorRotation(0.f, AimRotation.Yaw, 0.f);
	Pawn->SetActorRotation(ActorRotation);
}

void USCARARPoseSyncComponent::ApplyPoseToOwner(const FTransform& Pose, const bool bTeleport)
{
	AActor* Owner = GetOwner();
	if (!Owner)
	{
		return;
	}

	const FRotator AimRotation = Pose.Rotator();
	const FRotator UprightRotation(0.f, AimRotation.Yaw, 0.f);
	const FVector SnappedLocation = SnapLocationToSharedGround(Pose.GetLocation());

	Owner->SetActorLocationAndRotation(
		SnappedLocation,
		UprightRotation,
		false,
		nullptr,
		bTeleport ? ETeleportType::TeleportPhysics : ETeleportType::None);
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
	const FVector TargetLocation = SnapLocationToSharedGround(ProxyTargetPose.GetLocation());
	const FQuat TargetRotation = ProxyTargetPose.GetRotation();

	const float Alpha = FMath::Clamp(DeltaTime * ProxyInterpolationSpeed, 0.f, 1.f);
	const FVector NewLocation = FMath::Lerp(CurrentLocation, TargetLocation, Alpha);
	const FQuat NewRotation = FQuat::Slerp(CurrentRotation, TargetRotation, Alpha).GetNormalized();
	const FRotator NewRotator = NewRotation.Rotator();
	const FRotator UprightRotation(0.f, NewRotator.Yaw, 0.f);
	
	const FVector SnappedCurrentLocation = SnapLocationToSharedGround(CurrentLocation);
	const FVector SnappedNewLocation = SnapLocationToSharedGround(NewLocation);

	// Feed CharacterMovement velocity for ABP_Manny locomotion.
	// Since we manually move the pawn, CharacterMovement's velocity would otherwise stay 0
	// and locomotion would remain in idle.
	if (ACharacter* CharacterOwner = Cast<ACharacter>(Owner))
	{
		if (UCharacterMovementComponent* Movement = CharacterOwner->GetCharacterMovement())
		{
			const float SafeDt = FMath::Max(DeltaTime, KINDA_SMALL_NUMBER);
			const FVector Delta = (SnappedNewLocation - SnappedCurrentLocation) / SafeDt;
			Movement->Velocity = FVector(Delta.X, Delta.Y, 0.f);
		}
	}

	Owner->SetActorLocationAndRotation(
		SnappedNewLocation,
		UprightRotation,
		false,
		nullptr,
		ETeleportType::None);
}

void USCARARPoseSyncComponent::UpdateRemoteProxyPose(const float DeltaTime)
{
	AActor* Owner = GetOwner();
	if (Owner)
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
		// Even without a replicated AR pose yet, make sure the proxy doesn't
		// start floating above the world. This is critical for early join.
		if (!Owner)
		{
			return;
		}
		const FVector CurrentLocation = Owner->GetActorLocation();
		const FVector SnappedLocation = SnapLocationToSharedGround(CurrentLocation);
		if (!FMath::IsNearlyEqual(CurrentLocation.Z, SnappedLocation.Z, 1.f))
		{
			Owner->SetActorLocation(SnappedLocation, false, nullptr, ETeleportType::TeleportPhysics);
		}
		return;
	}

	ProxyTargetPose = ComputeWorldPoseFromSessionRelative(ReplicatedARPose);
	ProxyTargetPose.SetLocation(SnapLocationToSharedGround(ProxyTargetPose.GetLocation()));
	ProxyTargetPose.SetRotation(MakeUprightYawRotation(ProxyTargetPose.Rotator()).Quaternion());

	if (!bHasSnappedRemotePose)
	{
		LastRemoteLocationForVelocity = Owner->GetActorLocation();
		ApplyPoseToOwner(ProxyTargetPose, true);
		bHasSnappedRemotePose = true;
		return;
	}

	UpdateProxyInterpolation(DeltaTime);

	// Hard-lock Z every frame so look rotation cannot drift the proxy off the floor.
	const FVector CurrentLocation = Owner->GetActorLocation();
	const FVector SnappedLocation = SnapLocationToSharedGround(CurrentLocation);
	if (!FMath::IsNearlyEqual(CurrentLocation.Z, SnappedLocation.Z, 0.5f))
	{
		Owner->SetActorLocation(
			FVector(CurrentLocation.X, CurrentLocation.Y, SnappedLocation.Z),
			false,
			nullptr,
			ETeleportType::TeleportPhysics);
	}

	SCARAvatarGrounding::SnapPawnFeetToGround(Cast<APawn>(Owner));
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
