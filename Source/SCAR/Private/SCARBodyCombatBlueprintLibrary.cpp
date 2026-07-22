#include "SCARBodyCombatBlueprintLibrary.h"

#include "Engine/World.h"
#include "SCARBodyCombatSubsystem.h"
#include "SCARHorrorKitZombieBlueprintLibrary.h"

USCARBodyCombatSubsystem* USCARBodyCombatBlueprintLibrary::GetBodyCombatSubsystem(const UObject* WorldContextObject)
{
	if (const UWorld* World = GEngine
		? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::LogAndReturnNull)
		: nullptr)
	{
		return World->GetSubsystem<USCARBodyCombatSubsystem>();
	}

	return nullptr;
}

FVector2D USCARBodyCombatBlueprintLibrary::GetCombatAimViewport01(const UObject* WorldContextObject)
{
	return USCARBodyCombatSubsystem::GetCombatAimViewport01(WorldContextObject);
}

FSCARBodyCombatHitResult USCARBodyCombatBlueprintLibrary::TryApplyARBodyShot(
	const UObject* WorldContextObject,
	const float BaseDamage,
	const float CriticalMultiplier,
	const bool bRequirePersonInPreview)
{
	if (const FSCARZombieHitResult ZombieHit = USCARHorrorKitZombieBlueprintLibrary::TryApplyZombieHitScan(
		WorldContextObject,
		BaseDamage);
		ZombieHit.bHit)
	{
		return FSCARBodyCombatHitResult();
	}

	if (USCARBodyCombatSubsystem* Subsystem = GetBodyCombatSubsystem(WorldContextObject))
	{
		return Subsystem->TryApplyShot(
			WorldContextObject,
			BaseDamage,
			CriticalMultiplier,
			bRequirePersonInPreview);
	}

	return FSCARBodyCombatHitResult();
}

FSCARBodyCombatHitResult USCARBodyCombatBlueprintLibrary::TryApplyARBodyShotAfterPhysicsHit(
	const UObject* WorldContextObject,
	const float BaseDamage,
	const float CriticalMultiplier,
	const FHitResult& PhysicsHit,
	const bool bPhysicsBlockingHit,
	const bool bOnlyWhenPhysicsMissesEnemy,
	const bool bRequirePersonInPreview)
{
	if (bPhysicsBlockingHit)
	{
		if (const FSCARZombieHitResult ZombieHit = USCARHorrorKitZombieBlueprintLibrary::TryApplyZombieHitAfterPhysicsHit(
			WorldContextObject,
			BaseDamage,
			PhysicsHit,
			bPhysicsBlockingHit);
			ZombieHit.bHit)
		{
			return FSCARBodyCombatHitResult();
		}
	}

	if (bOnlyWhenPhysicsMissesEnemy && bPhysicsBlockingHit)
	{
		if (const AActor* HitActor = PhysicsHit.GetActor())
		{
			if (HitActor->GetClass()->GetName().Contains(TEXT("BP_Enemy")))
			{
				return FSCARBodyCombatHitResult();
			}
		}
	}

	return TryApplyARBodyShot(WorldContextObject, BaseDamage, CriticalMultiplier, bRequirePersonInPreview);
}
