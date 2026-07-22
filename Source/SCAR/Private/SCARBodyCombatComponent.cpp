#include "SCARBodyCombatComponent.h"

#include "Engine/World.h"
#include "SCARBodyCombatSubsystem.h"
#include "SCARHorrorKitZombieBlueprintLibrary.h"

USCARBodyCombatComponent::USCARBodyCombatComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void USCARBodyCombatComponent::BeginPlay()
{
	Super::BeginPlay();

	if (UWorld* World = GetWorld())
	{
		if (USCARBodyCombatSubsystem* CombatSubsystem = World->GetSubsystem<USCARBodyCombatSubsystem>())
		{
			CombatSubsystem->OnBodyHit.AddDynamic(this, &USCARBodyCombatComponent::HandleSubsystemBodyHit);
		}
	}
}

void USCARBodyCombatComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	Super::EndPlay(EndPlayReason);
}

void USCARBodyCombatComponent::HandleSubsystemBodyHit(const FSCARBodyCombatHitResult& HitResult)
{
	OnBodyHit.Broadcast(HitResult);
}

bool USCARBodyCombatComponent::ShouldTryARBodyShot(const FHitResult& PhysicsHit, const bool bPhysicsBlockingHit) const
{
	if (!bOnlyWhenPhysicsMissesEnemy)
	{
		return true;
	}

	if (!bPhysicsBlockingHit)
	{
		return true;
	}

	const AActor* HitActor = PhysicsHit.GetActor();
	if (!HitActor)
	{
		return true;
	}

	const FString ClassName = HitActor->GetClass()->GetName();
	return !ClassName.Contains(TEXT("BP_Enemy"));
}

FSCARBodyCombatHitResult USCARBodyCombatComponent::ProcessWeaponHitScan(
	const float BaseDamage,
	const float CriticalMultiplier,
	const FHitResult& PhysicsHit,
	const bool bPhysicsBlockingHit)
{
	if (!ShouldTryARBodyShot(PhysicsHit, bPhysicsBlockingHit))
	{
		if (const FSCARZombieHitResult ZombieHit = USCARHorrorKitZombieBlueprintLibrary::TryApplyZombieHitAfterPhysicsHit(
			this,
			BaseDamage,
			PhysicsHit,
			bPhysicsBlockingHit);
			ZombieHit.bHit)
		{
			return FSCARBodyCombatHitResult();
		}

		return FSCARBodyCombatHitResult();
	}

	return ProcessWeaponShot(BaseDamage, CriticalMultiplier);
}

FSCARBodyCombatHitResult USCARBodyCombatComponent::ProcessWeaponShot(
	const float BaseDamage,
	const float CriticalMultiplier)
{
	if (UWorld* World = GetWorld())
	{
		if (USCARBodyCombatSubsystem* CombatSubsystem = World->GetSubsystem<USCARBodyCombatSubsystem>())
		{
			return CombatSubsystem->TryApplyShot(this, BaseDamage, CriticalMultiplier, bRequirePersonInPreview);
		}
	}

	return FSCARBodyCombatHitResult();
}
