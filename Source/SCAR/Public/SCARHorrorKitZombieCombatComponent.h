#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SCARHorrorKitZombieCombatComponent.generated.h"

class APawn;

/**
 * Detects local weapon fire and applies damage + hit-react anims to
 * SCARHorrorKitZombieDirector-managed zombies. Works without BP_Item_Base wiring.
 */
UCLASS(ClassGroup = (SCAR), meta = (BlueprintSpawnableComponent))
class SCAR_API USCARHorrorKitZombieCombatComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	USCARHorrorKitZombieCombatComponent();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|HorrorKit", meta = (ClampMin = "100"))
	float TraceDistanceCm = 10000.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|HorrorKit", meta = (ClampMin = "1"))
	float DefaultShotDamage = 25.f;

protected:
	virtual void BeginPlay() override;
	virtual void TickComponent(
		float DeltaTime,
		ELevelTick TickType,
		FActorComponentTickFunction* ThisTickFunction) override;

private:
	void TryProcessLocalFire(APawn* LocalPawn);
	float ReadWeaponDamage(APawn* LocalPawn) const;
	bool DetectFireEdge(APawn* LocalPawn);

	float LastFireAlpha = 0.f;
	int32 LastKnownAmmo = -1;
	bool bHasKnownAmmo = false;
	double LastShotProcessedSeconds = -1000.0;
};
