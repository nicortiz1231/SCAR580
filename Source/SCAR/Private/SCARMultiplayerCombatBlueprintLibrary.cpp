#include "SCARMultiplayerCombatBlueprintLibrary.h"

#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "SCARARMultiplayerPlayerController.h"
#include "SCARMultiplayerCombatComponent.h"

bool USCARMultiplayerCombatBlueprintLibrary::IsMultiplayerSession(const UObject* WorldContextObject)
{
	return ASCARARMultiplayerPlayerController::IsMultiplayerSession(WorldContextObject);
}

static USCARMultiplayerCombatComponent* GetCombatComponentFromContext(const UObject* WorldContextObject)
{
	const UWorld* World = GEngine
		? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull)
		: nullptr;

	if (!World)
	{
		return nullptr;
	}

	const APlayerController* PC = World->GetFirstPlayerController();
	const APawn* Pawn = PC ? PC->GetPawn() : nullptr;
	return Pawn ? Pawn->FindComponentByClass<USCARMultiplayerCombatComponent>() : nullptr;
}

FSCARMultiplayerHitResult USCARMultiplayerCombatBlueprintLibrary::TryApplyMultiplayerOpponentShot(
	const UObject* WorldContextObject,
	const float BaseDamage,
	const float CriticalMultiplier)
{
	if (!IsMultiplayerSession(WorldContextObject))
	{
		return FSCARMultiplayerHitResult();
	}

	if (USCARMultiplayerCombatComponent* Combat = GetCombatComponentFromContext(WorldContextObject))
	{
		return Combat->ProcessWeaponShot(BaseDamage, CriticalMultiplier);
	}

	return FSCARMultiplayerHitResult();
}

FSCARMultiplayerHitResult USCARMultiplayerCombatBlueprintLibrary::TryApplyMultiplayerOpponentShotAfterPhysicsHit(
	const UObject* WorldContextObject,
	const float BaseDamage,
	const float CriticalMultiplier,
	const FHitResult& PhysicsHit,
	const bool bPhysicsBlockingHit)
{
	if (!IsMultiplayerSession(WorldContextObject))
	{
		return FSCARMultiplayerHitResult();
	}

	if (USCARMultiplayerCombatComponent* Combat = GetCombatComponentFromContext(WorldContextObject))
	{
		return Combat->ProcessWeaponHitScan(BaseDamage, CriticalMultiplier, PhysicsHit, bPhysicsBlockingHit);
	}

	return FSCARMultiplayerHitResult();
}
