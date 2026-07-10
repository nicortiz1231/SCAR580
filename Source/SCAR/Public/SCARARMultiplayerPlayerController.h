#pragma once

#include "SCARPlayerController.h"
#include "SCARARMultiplayerPlayerController.generated.h"

class USCARARMultiplayerMenuWidget;

UCLASS()
class SCAR_API ASCARARMultiplayerPlayerController : public ASCARPlayerController
{
	GENERATED_BODY()

public:
	ASCARARMultiplayerPlayerController();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Multiplayer")
	FString DefaultMapPath = TEXT("/Game/SCAR580/Maps/Map_AR");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Multiplayer")
	int32 DefaultPort = 7777;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Multiplayer")
	bool bShowMultiplayerMenuOnBeginPlay = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Multiplayer")
	TSubclassOf<USCARARMultiplayerMenuWidget> MultiplayerMenuWidgetClass;

	UFUNCTION(Exec, Category = "SCAR|Multiplayer")
	void HostARMultiplayer(const FString& MapOverride = TEXT(""));

	UFUNCTION(Exec, Category = "SCAR|Multiplayer")
	void JoinARMultiplayer(const FString& Address);

	UFUNCTION(BlueprintCallable, Category = "SCAR|Multiplayer")
	void HostARMultiplayerGame(const FString& MapOverride = TEXT(""));

	UFUNCTION(BlueprintCallable, Category = "SCAR|Multiplayer")
	void JoinARMultiplayerGame(const FString& Address);

	UFUNCTION(BlueprintCallable, Exec, Category = "SCAR|Multiplayer")
	void ShowMultiplayerMenu();

	UFUNCTION(BlueprintCallable, Exec, Category = "SCAR|Multiplayer")
	void HideMultiplayerMenu();

	USCARARMultiplayerMenuWidget* GetMultiplayerMenuWidget() const { return MultiplayerMenuWidget; }

	UFUNCTION(BlueprintPure, Category = "SCAR|Multiplayer")
	static bool IsMultiplayerSession(const UObject* WorldContextObject);

	UFUNCTION(BlueprintCallable, Category = "SCAR|Multiplayer")
	void NotifyMultiplayerConnectionStatus();

protected:
	virtual void BeginPlay() override;

private:
	UPROPERTY()
	TObjectPtr<USCARARMultiplayerMenuWidget> MultiplayerMenuWidget;
};
