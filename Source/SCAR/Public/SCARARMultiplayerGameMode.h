#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "SCARARMultiplayerGameMode.generated.h"

/** Two-player AR multiplayer prototype: listen-server host + one client. */
UCLASS()
class SCAR_API ASCARARMultiplayerGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	ASCARARMultiplayerGameMode();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Multiplayer")
	int32 MaxPlayers = 2;

protected:
	virtual void InitGame(const FString& MapName, const FString& Options, FString& ErrorMessage) override;
	virtual void StartPlay() override;
	virtual void GenericPlayerInitialization(AController* NewPlayer) override;
	virtual void PostLogin(APlayerController* NewPlayer) override;
	virtual AActor* ChoosePlayerStart_Implementation(AController* Player) override;
};
