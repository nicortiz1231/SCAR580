#include "SCARHorrorKitZombieBlueprintLibrary.h"

#include "Camera/PlayerCameraManager.h"
#include "Components/CapsuleComponent.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/PlayerController.h"
#include "SCARHorrorKitZombieDirector.h"

namespace SCARHorrorKitZombieBlueprintLibraryPrivate
{
	static ACharacter* ResolveZombieFromHit(const FHitResult& Hit)
	{
		if (ACharacter* Direct = Cast<ACharacter>(Hit.GetActor()))
		{
			return Direct;
		}

		if (const AActor* HitActor = Hit.GetActor())
		{
			if (ACharacter* Owner = Cast<ACharacter>(HitActor->GetOwner()))
			{
				return Owner;
			}
		}

		if (const UPrimitiveComponent* Comp = Hit.GetComponent())
		{
			if (ACharacter* Owner = Cast<ACharacter>(Comp->GetOwner()))
			{
				return Owner;
			}
		}

		return nullptr;
	}

	static FSCARZombieHitResult ApplyToResolvedZombie(
		const UObject* WorldContextObject,
		ACharacter* Enemy,
		const float Damage)
	{
		FSCARZombieHitResult Result;
		if (!IsValid(Enemy) || Damage <= 0.f)
		{
			return Result;
		}

		UWorld* World = GEngine
			? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull)
			: nullptr;
		if (!World)
		{
			return Result;
		}

		ASCARHorrorKitZombieDirector* Director = ASCARHorrorKitZombieDirector::EnsureInWorld(World);
		if (!Director || !Director->IsManagedEnemy(Enemy))
		{
			return Result;
		}

		return Director->NotifyEnemyShot(Enemy, Damage);
	}

	static ACharacter* TraceManagedZombie(
		const UWorld* World,
		const ASCARHorrorKitZombieDirector* Director,
		const FVector& TraceStart,
		const FVector& TraceEnd,
		const AActor* IgnoreActor)
	{
		if (!World || !Director)
		{
			return nullptr;
		}

		FCollisionQueryParams Params(SCENE_QUERY_STAT(SCARZombieHitScan), true, IgnoreActor);
		Params.bReturnPhysicalMaterial = false;

		FCollisionObjectQueryParams ObjectParams;
		ObjectParams.AddObjectTypesToQuery(ECC_Pawn);
		ObjectParams.AddObjectTypesToQuery(ECC_WorldDynamic);
		ObjectParams.AddObjectTypesToQuery(ECC_PhysicsBody);
		ObjectParams.AddObjectTypesToQuery(ECC_Visibility);

		TArray<FHitResult> Hits;
		if (World->LineTraceMultiByObjectType(Hits, TraceStart, TraceEnd, ObjectParams, Params))
		{
			for (const FHitResult& Hit : Hits)
			{
				ACharacter* Enemy = ResolveZombieFromHit(Hit);
				if (IsValid(Enemy) && Director->IsManagedEnemy(Enemy))
				{
					return Enemy;
				}
			}
		}

		FHitResult VisibilityHit;
		if (World->LineTraceSingleByChannel(VisibilityHit, TraceStart, TraceEnd, ECC_Visibility, Params))
		{
			ACharacter* Enemy = ResolveZombieFromHit(VisibilityHit);
			if (IsValid(Enemy) && Director->IsManagedEnemy(Enemy))
			{
				return Enemy;
			}
		}

		const FVector ViewDir = (TraceEnd - TraceStart).GetSafeNormal();
		const float MaxDistance = FVector::Dist(TraceStart, TraceEnd);
		return Director->FindManagedEnemyUnderCrosshair(TraceStart, ViewDir, MaxDistance);
	}
}

FSCARZombieHitResult USCARHorrorKitZombieBlueprintLibrary::TryApplyZombieHitScan(
	const UObject* WorldContextObject,
	const float Damage,
	const float TraceDistance)
{
	FSCARZombieHitResult Result;

	UWorld* World = GEngine
		? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull)
		: nullptr;
	if (!World || Damage <= 0.f)
	{
		return Result;
	}

	const APlayerController* PC = World->GetFirstPlayerController();
	if (!PC)
	{
		return Result;
	}

	ASCARHorrorKitZombieDirector* Director = ASCARHorrorKitZombieDirector::EnsureInWorld(World);
	if (!Director)
	{
		return Result;
	}

	FVector TraceStart;
	FRotator ViewRotation;
	PC->GetPlayerViewPoint(TraceStart, ViewRotation);
	const FVector TraceEnd = TraceStart + ViewRotation.Vector() * FMath::Max(TraceDistance, 100.f);

	ACharacter* Enemy = SCARHorrorKitZombieBlueprintLibraryPrivate::TraceManagedZombie(
		World,
		Director,
		TraceStart,
		TraceEnd,
		PC->GetPawn());

	if (!Enemy)
	{
		return Result;
	}

	return SCARHorrorKitZombieBlueprintLibraryPrivate::ApplyToResolvedZombie(WorldContextObject, Enemy, Damage);
}

FSCARZombieHitResult USCARHorrorKitZombieBlueprintLibrary::TryApplyZombieHitAfterPhysicsHit(
	const UObject* WorldContextObject,
	const float Damage,
	const FHitResult& PhysicsHit,
	const bool bPhysicsBlockingHit)
{
	if (!bPhysicsBlockingHit || Damage <= 0.f)
	{
		return FSCARZombieHitResult();
	}

	ACharacter* Enemy = SCARHorrorKitZombieBlueprintLibraryPrivate::ResolveZombieFromHit(PhysicsHit);
	return SCARHorrorKitZombieBlueprintLibraryPrivate::ApplyToResolvedZombie(WorldContextObject, Enemy, Damage);
}
