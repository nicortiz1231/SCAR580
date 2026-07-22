#pragma once

#include "CoreMinimal.h"
#include "Engine/HitResult.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "SCARHorrorKitZombieTypes.h"
#include "SCARHorrorKitZombieBlueprintLibrary.generated.h"

UCLASS()
class SCAR_API USCARHorrorKitZombieBlueprintLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/** Camera line trace for a director-managed zombie. */
	UFUNCTION(BlueprintCallable, Category = "SCAR|HorrorKit", meta = (WorldContext = "WorldContextObject"))
	static FSCARZombieHitResult TryApplyZombieHitScan(
		const UObject* WorldContextObject,
		float Damage,
		float TraceDistance = 10000.f);

	/** Use the weapon physics hit when it already struck something. */
	UFUNCTION(BlueprintCallable, Category = "SCAR|HorrorKit", meta = (WorldContext = "WorldContextObject"))
	static FSCARZombieHitResult TryApplyZombieHitAfterPhysicsHit(
		const UObject* WorldContextObject,
		float Damage,
		const FHitResult& PhysicsHit,
		bool bPhysicsBlockingHit);
};
