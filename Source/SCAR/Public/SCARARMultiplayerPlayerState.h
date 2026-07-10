#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerState.h"
#include "SCARARMultiplayerPlayerState.generated.h"

UCLASS()
class SCAR_API ASCARARMultiplayerPlayerState : public APlayerState
{
	GENERATED_BODY()

public:
	ASCARARMultiplayerPlayerState();

	UPROPERTY(BlueprintReadOnly, ReplicatedUsing = OnRep_Kills, Category = "SCAR|Multiplayer")
	int32 Kills = 0;

	UPROPERTY(BlueprintReadOnly, ReplicatedUsing = OnRep_Deaths, Category = "SCAR|Multiplayer")
	int32 Deaths = 0;

	UFUNCTION(BlueprintCallable, Category = "SCAR|Multiplayer")
	void RegisterKill();

	UFUNCTION(BlueprintCallable, Category = "SCAR|Multiplayer")
	void RegisterDeath();

protected:
	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	UFUNCTION()
	void OnRep_Kills();

	UFUNCTION()
	void OnRep_Deaths();
};
