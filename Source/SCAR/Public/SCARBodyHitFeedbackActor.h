#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SCARBodyHitFeedbackActor.generated.h"

class UNiagaraComponent;
class UNiagaraSystem;

UCLASS()
class SCAR_API ASCARBodyHitFeedbackActor : public AActor
{
	GENERATED_BODY()

public:
	ASCARBodyHitFeedbackActor();

	void SpawnBloodEffect();
	void ActivateAtLocation(const FVector& WorldLocation);

protected:
	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<USceneComponent> Root;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UNiagaraComponent> BloodEffect;

	UPROPERTY(EditDefaultsOnly, Category = "SCAR|Body Combat")
	TObjectPtr<UNiagaraSystem> BloodNiagaraSystem;

	UPROPERTY(EditDefaultsOnly, Category = "SCAR|Body Combat")
	float BloodLifetimeSeconds = 0.45f;

private:
	FTimerHandle BloodDestroyTimerHandle;
};
