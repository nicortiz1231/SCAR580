#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SCARMultiplayerTypes.h"
#include "SCARMultiplayerCombatComponent.generated.h"

UCLASS(ClassGroup = (SCAR), meta = (BlueprintSpawnableComponent))
class SCAR_API USCARMultiplayerCombatComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	USCARMultiplayerCombatComponent();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Multiplayer|Combat")
	float TraceDistance = 100000.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Multiplayer|Combat")
	float HeadshotHeightFraction = 0.82f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Multiplayer|Combat")
	float HeadshotDamageMultiplier = 2.f;

	UPROPERTY(BlueprintAssignable, Category = "SCAR|Multiplayer|Combat")
	FSCARMultiplayerHitDelegate OnOpponentHit;

	UFUNCTION(BlueprintCallable, Category = "SCAR|Multiplayer|Combat")
	FSCARMultiplayerHitResult ProcessWeaponShot(float BaseDamage, float CriticalMultiplier);

	UFUNCTION(BlueprintCallable, Category = "SCAR|Multiplayer|Combat")
	FSCARMultiplayerHitResult ProcessWeaponHitScan(
		float BaseDamage,
		float CriticalMultiplier,
		const FHitResult& PhysicsHit,
		bool bPhysicsBlockingHit);

protected:
	virtual void BeginPlay() override;

private:
	bool IsOpponentPawn(const APawn* TargetPawn, const APawn* ShooterPawn) const;
	bool IsHeadshot(const APawn* TargetPawn, const FVector& HitLocation) const;
	FSCARMultiplayerHitResult TraceForOpponent(float BaseDamage, float CriticalMultiplier);
	FSCARMultiplayerHitResult ApplyHitToPawn(APawn* HitPawn, float Damage, bool bHeadshot);

	UFUNCTION(Server, Reliable)
	void Server_ReportHit(APawn* HitPawn, float Damage, bool bHeadshot, FVector_NetQuantize HitLocation);
};
