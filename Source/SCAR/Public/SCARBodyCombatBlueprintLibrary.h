#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "SCARBodyCombatTypes.h"
#include "SCARBodyCombatBlueprintLibrary.generated.h"

class USCARBodyCombatSubsystem;

UCLASS()
class SCAR_API USCARBodyCombatBlueprintLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintPure, Category = "SCAR|Body Combat", meta = (WorldContext = "WorldContextObject"))
	static USCARBodyCombatSubsystem* GetBodyCombatSubsystem(const UObject* WorldContextObject);

	UFUNCTION(BlueprintPure, Category = "SCAR|Body Combat", meta = (WorldContext = "WorldContextObject"))
	static FVector2D GetCombatAimViewport01(const UObject* WorldContextObject);

	UFUNCTION(BlueprintCallable, Category = "SCAR|Body Combat", meta = (WorldContext = "WorldContextObject"))
	static FSCARBodyCombatHitResult TryApplyARBodyShot(
		const UObject* WorldContextObject,
		float BaseDamage,
		float CriticalMultiplier,
		bool bRequirePersonInPreview = true);

	UFUNCTION(BlueprintCallable, Category = "SCAR|Body Combat", meta = (WorldContext = "WorldContextObject"))
	static FSCARBodyCombatHitResult TryApplyARBodyShotAfterPhysicsHit(
		const UObject* WorldContextObject,
		float BaseDamage,
		float CriticalMultiplier,
		const FHitResult& PhysicsHit,
		bool bPhysicsBlockingHit,
		bool bOnlyWhenPhysicsMissesEnemy = true,
		bool bRequirePersonInPreview = true);
};
