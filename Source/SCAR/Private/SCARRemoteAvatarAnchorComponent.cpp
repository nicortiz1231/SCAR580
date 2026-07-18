#include "SCARRemoteAvatarAnchorComponent.h"

#include "ARBlueprintLibrary.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerState.h"
#include "GameFramework/Pawn.h"
#include "HeadMountedDisplayFunctionLibrary.h"

USCARRemoteAvatarAnchorComponent::USCARRemoteAvatarAnchorComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	// After replication, movement, and every gameplay tick have written pawn
	// transforms for this frame, so our counter-roll is the final word before
	// rendering.
	PrimaryComponentTick.TickGroup = TG_LastDemotable;
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
		RestoreAnchoredPawns();
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

	// Rotation by -DeviceRoll around the local camera's forward axis, pivoting
	// at the camera origin. FRotator(P,Y,R) equals FRotator(P,Y,0) followed by
	// a roll about the resulting forward axis, so conjugating a pure-roll
	// rotator by the camera rotation yields exactly the view-axis roll the
	// render camera ignored.
	const FQuat CameraQuat = ViewRotation.Quaternion();
	const FQuat CounterRollWorld =
		CameraQuat * FRotator(0.f, 0.f, -DeviceRollDegrees).Quaternion() * CameraQuat.Inverse();

	const APawn* LocalPawn = LocalPC->GetPawn();

	// Drop entries for pawns that no longer exist.
	for (auto It = AnchoredPawns.CreateIterator(); It; ++It)
	{
		if (!It.Key().IsValid())
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

		// Only anchor other PLAYERS' avatars.
		if (!Pawn->GetPlayerState())
		{
			continue;
		}

		FAnchorState& State = AnchoredPawns.FindOrAdd(Pawn);

		// If nothing else moved the pawn since our last write, reuse the
		// remembered un-rolled base; if replication/movement DID move it, that
		// fresh pose becomes the new base. The roll is therefore always
		// applied to an un-rolled pose exactly once and never compounds.
		const FTransform CurrentWorld = Pawn->GetActorTransform();
		const bool bUnchangedSinceLastWrite =
			CurrentWorld.GetLocation().Equals(State.LastSetWorld.GetLocation(), 0.01f) &&
			CurrentWorld.GetRotation().Equals(State.LastSetWorld.GetRotation(), 0.0001f);

		const FTransform BaseWorld = bUnchangedSinceLastWrite ? State.BaseWorld : CurrentWorld;

		const FVector AnchoredLocation =
			ViewLocation + CounterRollWorld.RotateVector(BaseWorld.GetLocation() - ViewLocation);
		const FQuat AnchoredRotation = (CounterRollWorld * BaseWorld.GetRotation()).GetNormalized();

		Pawn->SetActorLocationAndRotation(
			AnchoredLocation,
			AnchoredRotation,
			false,
			nullptr,
			ETeleportType::TeleportPhysics);

		State.BaseWorld = BaseWorld;
		State.LastSetWorld = FTransform(AnchoredRotation, AnchoredLocation, CurrentWorld.GetScale3D());
	}
}

void USCARRemoteAvatarAnchorComponent::RestoreAnchoredPawns()
{
	for (auto& Pair : AnchoredPawns)
	{
		APawn* Pawn = Cast<APawn>(Pair.Key.Get());
		if (!Pawn)
		{
			continue;
		}

		// Only put the pawn back if it is still exactly where we left it.
		const FTransform CurrentWorld = Pawn->GetActorTransform();
		if (CurrentWorld.GetLocation().Equals(Pair.Value.LastSetWorld.GetLocation(), 0.01f) &&
			CurrentWorld.GetRotation().Equals(Pair.Value.LastSetWorld.GetRotation(), 0.0001f))
		{
			Pawn->SetActorLocationAndRotation(
				Pair.Value.BaseWorld.GetLocation(),
				Pair.Value.BaseWorld.GetRotation(),
				false,
				nullptr,
				ETeleportType::TeleportPhysics);
		}
	}

	AnchoredPawns.Empty();
}
