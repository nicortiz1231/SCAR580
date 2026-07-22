#include "SCARMultiplayerPawnSetup.h"

#include "ARBlueprintLibrary.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/Pawn.h"
#include "SCARARPoseSyncComponent.h"
#include "SCARAvatarGrounding.h"
#include "SCARMultiplayerCombatComponent.h"
#include "SCARMultiplayerHealthComponent.h"
#include "SCARMultiplayerPresentationComponent.h"
#include "SCARHorrorKitZombieCombatComponent.h"
#include "SCARSharedARGround.h"

namespace SCARMultiplayerPawnSetup
{
	template<typename TComponent>
	TComponent* EnsureComponent(APawn* Pawn, const FName ComponentName)
	{
		if (!Pawn)
		{
			return nullptr;
		}

		if (TComponent* Existing = Pawn->FindComponentByClass<TComponent>())
		{
			return Existing;
		}

		TComponent* NewComponent = NewObject<TComponent>(Pawn, ComponentName);
		if (!NewComponent)
		{
			return nullptr;
		}

		Pawn->AddInstanceComponent(NewComponent);
		NewComponent->RegisterComponent();

		if (GEngine)
		{
			GEngine->AddOnScreenDebugMessage(
				-1,
				8.f,
				FColor::Green,
				FString::Printf(TEXT("SCAR: Added %s to %s at runtime"), *ComponentName.ToString(), *Pawn->GetName()));
		}

		return NewComponent;
	}

	void EnsureMultiplayerFloor(UWorld* World)
	{
		if (!World || ASCARSharedARGround::FindInWorld(World))
		{
			return;
		}

		// On device AR the floor is placed at the player's feet when the session origin is captured.
		const FARSessionStatus ARStatus = UARBlueprintLibrary::GetARSessionStatus();
		if (ARStatus.Status == EARSessionStatus::Running)
		{
			return;
		}

#if !PLATFORM_IOS
		FActorSpawnParameters SpawnParams;
		SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

		ASCARSharedARGround* Ground = World->SpawnActor<ASCARSharedARGround>(
			ASCARSharedARGround::StaticClass(),
			FVector::ZeroVector,
			FRotator::ZeroRotator,
			SpawnParams);
		if (!Ground)
		{
			return;
		}

		Ground->PlaceAt(FVector::ZeroVector, 0.f);

		if (GEngine)
		{
			GEngine->AddOnScreenDebugMessage(
				9100,
				10.f,
				FColor::Green,
				TEXT("SCAR: Multiplayer floor spawned (Z=0)"));
		}
#endif
	}

	void SnapPawnToGround(APawn* Pawn)
	{
		if (!Pawn)
		{
			return;
		}

		float CapsuleHalfHeight = 88.f;
		if (const UCapsuleComponent* Capsule = Pawn->FindComponentByClass<UCapsuleComponent>())
		{
			CapsuleHalfHeight = Capsule->GetScaledCapsuleHalfHeight();
		}

		float GroundZ = 0.f;
		const FVector PawnLocation = Pawn->GetActorLocation();
		if (!SCARAvatarGrounding::TraceGroundWorldZ(Pawn->GetWorld(), PawnLocation, PawnLocation.Z - CapsuleHalfHeight, GroundZ, Pawn))
		{
			GroundZ = 0.f;
		}

		const float TargetZ = GroundZ + CapsuleHalfHeight;
		if (!FMath::IsNearlyEqual(PawnLocation.Z, TargetZ, 0.5f))
		{
			Pawn->SetActorLocation(
				FVector(PawnLocation.X, PawnLocation.Y, TargetZ),
				false,
				nullptr,
				ETeleportType::TeleportPhysics);
		}

		if (USkeletalMeshComponent* BodyMesh = SCARAvatarGrounding::FindBodyMesh(Pawn))
		{
			if (ACharacter* Character = Cast<ACharacter>(Pawn))
			{
				if (const UCapsuleComponent* Capsule = Character->GetCapsuleComponent())
				{
					const float DesiredMeshZ = -Capsule->GetScaledCapsuleHalfHeight();
					const FVector RelativeLocation = BodyMesh->GetRelativeLocation();
					if (!FMath::IsNearlyEqual(RelativeLocation.Z, DesiredMeshZ, 1.f))
					{
						BodyMesh->SetRelativeLocation(FVector(RelativeLocation.X, RelativeLocation.Y, DesiredMeshZ));
					}
				}
			}
		}
	}

	void EnsureMultiplayerPawnComponents(APawn* Pawn)
	{
		if (!Pawn || !Pawn->IsPlayerControlled())
		{
			return;
		}

		EnsureMultiplayerFloor(Pawn->GetWorld());

		EnsureComponent<USCARARPoseSyncComponent>(Pawn, TEXT("SCARARPoseSync"));
		EnsureComponent<USCARMultiplayerPresentationComponent>(Pawn, TEXT("SCARMultiplayerPresentation"));
		EnsureComponent<USCARMultiplayerHealthComponent>(Pawn, TEXT("SCARMultiplayerHealth"));
		EnsureComponent<USCARMultiplayerCombatComponent>(Pawn, TEXT("SCARMultiplayerCombat"));
		EnsureComponent<USCARHorrorKitZombieCombatComponent>(Pawn, TEXT("SCARHorrorKitZombieCombat"));

		if (ACharacter* Character = Cast<ACharacter>(Pawn))
		{
			if (UCharacterMovementComponent* Movement = Character->GetCharacterMovement())
			{
				Movement->GravityScale = 1.f;
				Movement->SetMovementMode(MOVE_Walking);
			}
		}

		SnapPawnToGround(Pawn);
	}
}
