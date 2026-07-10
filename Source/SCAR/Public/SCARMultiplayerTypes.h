#pragma once

#include "CoreMinimal.h"
#include "SCARMultiplayerTypes.generated.h"

USTRUCT(BlueprintType)
struct SCAR_API FSCARMultiplayerHitResult
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Multiplayer")
	bool bHit = false;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Multiplayer")
	bool bIsHeadshot = false;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Multiplayer")
	bool bKilledTarget = false;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Multiplayer")
	float AppliedDamage = 0.f;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Multiplayer")
	float RemainingHealth = 0.f;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Multiplayer")
	TWeakObjectPtr<AActor> HitActor;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Multiplayer")
	FVector HitLocation = FVector::ZeroVector;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FSCARMultiplayerHitDelegate, const FSCARMultiplayerHitResult&, HitResult);
