#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SCARBodyCombatTypes.h"
#include "SCARBodyCombatComponent.generated.h"

UCLASS(ClassGroup = (SCAR), meta = (BlueprintSpawnableComponent))
class SCAR_API USCARBodyCombatComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	USCARBodyCombatComponent();

	UPROPERTY(BlueprintAssignable, Category = "SCAR|Body Combat")
	FSCARBodyCombatHitDelegate OnBodyHit;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Combat")
	bool bOnlyWhenPhysicsMissesEnemy = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Combat")
	bool bRequirePersonInPreview = true;

	UFUNCTION(BlueprintCallable, Category = "SCAR|Body Combat")
	FSCARBodyCombatHitResult ProcessWeaponHitScan(
		float BaseDamage,
		float CriticalMultiplier,
		const FHitResult& PhysicsHit,
		bool bPhysicsBlockingHit);

	UFUNCTION(BlueprintCallable, Category = "SCAR|Body Combat")
	FSCARBodyCombatHitResult ProcessWeaponShot(float BaseDamage, float CriticalMultiplier);

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
	UFUNCTION()
	void HandleSubsystemBodyHit(const FSCARBodyCombatHitResult& HitResult);

	bool ShouldTryARBodyShot(const FHitResult& PhysicsHit, bool bPhysicsBlockingHit) const;
};
