#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "SCARMultiplayerTypes.h"
#include "SCARMultiplayerCombatBlueprintLibrary.generated.h"

UCLASS()
class SCAR_API USCARMultiplayerCombatBlueprintLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintPure, Category = "SCAR|Multiplayer", meta = (WorldContext = "WorldContextObject"))
	static bool IsMultiplayerSession(const UObject* WorldContextObject);

	UFUNCTION(BlueprintCallable, Category = "SCAR|Multiplayer", meta = (WorldContext = "WorldContextObject"))
	static FSCARMultiplayerHitResult TryApplyMultiplayerOpponentShot(
		const UObject* WorldContextObject,
		float BaseDamage,
		float CriticalMultiplier);

	UFUNCTION(BlueprintCallable, Category = "SCAR|Multiplayer", meta = (WorldContext = "WorldContextObject"))
	static FSCARMultiplayerHitResult TryApplyMultiplayerOpponentShotAfterPhysicsHit(
		const UObject* WorldContextObject,
		float BaseDamage,
		float CriticalMultiplier,
		const FHitResult& PhysicsHit,
		bool bPhysicsBlockingHit);
};
