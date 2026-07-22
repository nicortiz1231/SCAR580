#pragma once

#include "CoreMinimal.h"
#include "SCARHorrorKitZombieTypes.generated.h"

class ACharacter;

USTRUCT(BlueprintType)
struct FSCARZombieHitResult
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|HorrorKit")
	bool bHit = false;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|HorrorKit")
	float AppliedDamage = 0.f;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|HorrorKit")
	float RemainingHealth = 0.f;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|HorrorKit")
	bool bKilled = false;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|HorrorKit")
	TObjectPtr<ACharacter> HitEnemy = nullptr;
};
