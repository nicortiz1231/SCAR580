#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SCARMultiplayerTypes.h"
#include "SCARMultiplayerHealthComponent.generated.h"

UCLASS(ClassGroup = (SCAR), meta = (BlueprintSpawnableComponent))
class SCAR_API USCARMultiplayerHealthComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	USCARMultiplayerHealthComponent();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Multiplayer|Health")
	float MaxHealth = 100.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Multiplayer|Health")
	float RespawnDelaySeconds = 4.f;

	UPROPERTY(BlueprintAssignable, Category = "SCAR|Multiplayer|Health")
	FSCARMultiplayerHitDelegate OnDamageTaken;

	UPROPERTY(BlueprintReadOnly, ReplicatedUsing = OnRep_Health, Category = "SCAR|Multiplayer|Health")
	float Health = 100.f;

	UFUNCTION(BlueprintPure, Category = "SCAR|Multiplayer|Health")
	bool IsAlive() const { return Health > 0.f; }

	UFUNCTION(BlueprintCallable, Category = "SCAR|Multiplayer|Health")
	float ApplyDamage(float Damage, AActor* DamageCauser, bool bHeadshot);

protected:
	virtual void BeginPlay() override;
	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	UFUNCTION()
	void OnRep_Health();

private:
	void ResetHealth();
	void HandleDeath();
};
