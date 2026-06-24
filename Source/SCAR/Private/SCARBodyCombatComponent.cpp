#include "SCARBodyCombatComponent.h"

#include "Debug/DebugDrawService.h"
#include "Engine/Canvas.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "SCARBodyCombatSubsystem.h"

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

	if (!HitMarkerOverlayDrawHandle.IsValid())
	{
		FDebugDrawDelegate DebugDrawDelegate;
		DebugDrawDelegate.BindUObject(this, &USCARBodyCombatComponent::OnHitMarkerOverlayDraw);
		HitMarkerOverlayDrawHandle = UDebugDrawService::Register(TEXT("Game"), DebugDrawDelegate);
	}
}

void USCARBodyCombatComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (HitMarkerOverlayDrawHandle.IsValid())
	{
		UDebugDrawService::Unregister(HitMarkerOverlayDrawHandle);
		HitMarkerOverlayDrawHandle.Reset();
	}

	Super::EndPlay(EndPlayReason);
}

void USCARBodyCombatComponent::OnHitMarkerOverlayDraw(UCanvas* Canvas, APlayerController* PlayerController)
{
	if (!Canvas || !PlayerController)
	{
		return;
	}

	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	USCARBodyCombatSubsystem* CombatSubsystem = World->GetSubsystem<USCARBodyCombatSubsystem>();
	if (!CombatSubsystem)
	{
		return;
	}

	CombatSubsystem->DrawSkeletonHitMarkerOverlay(Canvas, PlayerController);
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
