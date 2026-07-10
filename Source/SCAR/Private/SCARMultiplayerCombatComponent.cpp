#include "SCARMultiplayerCombatComponent.h"

#include "Camera/PlayerCameraManager.h"
#include "Components/CapsuleComponent.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/PlayerController.h"
#include "SCARARMultiplayerPlayerController.h"
#include "SCARMultiplayerHealthComponent.h"

USCARMultiplayerCombatComponent::USCARMultiplayerCombatComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
	SetIsReplicatedByDefault(true);
}

void USCARMultiplayerCombatComponent::BeginPlay()
{
	Super::BeginPlay();
}

FSCARMultiplayerHitResult USCARMultiplayerCombatComponent::ProcessWeaponShot(
	const float BaseDamage,
	const float CriticalMultiplier)
{
	if (!ASCARARMultiplayerPlayerController::IsMultiplayerSession(GetWorld()))
	{
		return FSCARMultiplayerHitResult();
	}

	return TraceForOpponent(BaseDamage, CriticalMultiplier);
}

FSCARMultiplayerHitResult USCARMultiplayerCombatComponent::ProcessWeaponHitScan(
	const float BaseDamage,
	const float CriticalMultiplier,
	const FHitResult& PhysicsHit,
	const bool bPhysicsBlockingHit)
{
	APawn* OwnerPawn = Cast<APawn>(GetOwner());
	if (!OwnerPawn || !OwnerPawn->IsLocallyControlled())
	{
		return FSCARMultiplayerHitResult();
	}

	if (bPhysicsBlockingHit)
	{
		if (APawn* HitPawn = Cast<APawn>(PhysicsHit.GetActor()))
		{
			if (IsOpponentPawn(HitPawn, OwnerPawn))
			{
				const bool bHeadshot = IsHeadshot(HitPawn, PhysicsHit.ImpactPoint);
				const float Damage = BaseDamage * (bHeadshot ? CriticalMultiplier : 1.f);
				Server_ReportHit(HitPawn, Damage, bHeadshot, PhysicsHit.ImpactPoint);
				return ApplyHitToPawn(HitPawn, Damage, bHeadshot);
			}
		}
	}

	return TraceForOpponent(BaseDamage, CriticalMultiplier);
}

FSCARMultiplayerHitResult USCARMultiplayerCombatComponent::TraceForOpponent(
	const float BaseDamage,
	const float CriticalMultiplier)
{
	APawn* OwnerPawn = Cast<APawn>(GetOwner());
	if (!OwnerPawn || !OwnerPawn->IsLocallyControlled())
	{
		return FSCARMultiplayerHitResult();
	}

	APlayerController* PC = Cast<APlayerController>(OwnerPawn->GetController());
	if (!PC)
	{
		return FSCARMultiplayerHitResult();
	}

	FVector TraceStart;
	FRotator ViewRotation;
	PC->GetPlayerViewPoint(TraceStart, ViewRotation);
	const FVector TraceEnd = TraceStart + ViewRotation.Vector() * TraceDistance;

	FCollisionQueryParams Params(SCENE_QUERY_STAT(SCARMultiplayerShot), true, OwnerPawn);
	Params.bReturnPhysicalMaterial = false;

	FHitResult Hit;
	UWorld* World = GetWorld();
	if (!World || !World->LineTraceSingleByChannel(Hit, TraceStart, TraceEnd, ECC_Visibility, Params))
	{
		return FSCARMultiplayerHitResult();
	}

	APawn* HitPawn = Cast<APawn>(Hit.GetActor());
	if (!HitPawn || !IsOpponentPawn(HitPawn, OwnerPawn))
	{
		if (AActor* HitOwner = Hit.GetActor())
		{
			HitPawn = Cast<APawn>(HitOwner->GetOwner());
		}
	}

	if (!HitPawn || !IsOpponentPawn(HitPawn, OwnerPawn))
	{
		return FSCARMultiplayerHitResult();
	}

	const bool bHeadshot = IsHeadshot(HitPawn, Hit.ImpactPoint);
	const float Damage = BaseDamage * (bHeadshot ? CriticalMultiplier : 1.f);
	Server_ReportHit(HitPawn, Damage, bHeadshot, Hit.ImpactPoint);
	return ApplyHitToPawn(HitPawn, Damage, bHeadshot);
}

FSCARMultiplayerHitResult USCARMultiplayerCombatComponent::ApplyHitToPawn(
	APawn* HitPawn,
	const float Damage,
	const bool bHeadshot)
{
	FSCARMultiplayerHitResult Result;
	Result.bHit = true;
	Result.bIsHeadshot = bHeadshot;
	Result.AppliedDamage = Damage;
	Result.HitActor = HitPawn;

	if (USCARMultiplayerHealthComponent* Health = HitPawn->FindComponentByClass<USCARMultiplayerHealthComponent>())
	{
		Result.RemainingHealth = Health->Health;
		Result.bKilledTarget = Health->Health <= 0.f;
	}

	OnOpponentHit.Broadcast(Result);
	return Result;
}

bool USCARMultiplayerCombatComponent::IsOpponentPawn(
	const APawn* TargetPawn,
	const APawn* ShooterPawn) const
{
	if (!TargetPawn || !ShooterPawn || TargetPawn == ShooterPawn)
	{
		return false;
	}

	if (!TargetPawn->IsPlayerControlled())
	{
		return false;
	}

	return ASCARARMultiplayerPlayerController::IsMultiplayerSession(GetWorld());
}

bool USCARMultiplayerCombatComponent::IsHeadshot(
	const APawn* TargetPawn,
	const FVector& HitLocation) const
{
	if (!TargetPawn)
	{
		return false;
	}

	float CapsuleHalfHeight = 88.f;
	if (const UCapsuleComponent* Capsule = TargetPawn->FindComponentByClass<UCapsuleComponent>())
	{
		CapsuleHalfHeight = Capsule->GetScaledCapsuleHalfHeight();
	}

	const float CapsuleBottomZ = TargetPawn->GetActorLocation().Z - CapsuleHalfHeight;
	const float CapsuleTopZ = TargetPawn->GetActorLocation().Z + CapsuleHalfHeight;
	const float HeightFraction = (HitLocation.Z - CapsuleBottomZ) / FMath::Max(CapsuleTopZ - CapsuleBottomZ, 1.f);
	return HeightFraction >= HeadshotHeightFraction;
}

void USCARMultiplayerCombatComponent::Server_ReportHit_Implementation(
	APawn* HitPawn,
	const float Damage,
	const bool bHeadshot,
	const FVector_NetQuantize HitLocation)
{
	if (!HitPawn || Damage <= 0.f)
	{
		return;
	}

	APawn* OwnerPawn = Cast<APawn>(GetOwner());
	if (!OwnerPawn || !IsOpponentPawn(HitPawn, OwnerPawn))
	{
		return;
	}

	if (USCARMultiplayerHealthComponent* Health = HitPawn->FindComponentByClass<USCARMultiplayerHealthComponent>())
	{
		Health->ApplyDamage(Damage, OwnerPawn, bHeadshot);
	}
}
