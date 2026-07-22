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
	virtual void SetupInputComponent() override;
	virtual bool InputKey(const FInputKeyEventArgs& Params) override;
	virtual bool InputTouch(
		const FTouchId TouchId,
		const ETouchType::Type Type,
		const FVector2D& TouchLocation,
		const float Force,
		const uint64 Timestamp) override;
	virtual void OnPossess(APawn* InPawn) override;
	virtual void PlayerTick(float DeltaTime) override;

	/** Tab — open/close pause inventory menu. */
	void OnToggleInventoryPressed();

	/** Duplicate TI_MobileCombat and inject a top-right Tab zone at runtime. */
	void EnsureMobileTouchInterface();

	/** Poll top-right Inventory launcher touches on mobile. */
	void PollMobileInventoryLauncher();

private:
	UPROPERTY()
	TObjectPtr<USCARARMultiplayerMenuWidget> MultiplayerMenuWidget;

	void EnsureLocalFirstPersonArms();
	void EnsureRemoteAvatarAnchor();
	void EnsureAvatarWeaponSync();

	/** Upgrade PoseTracking AR session to World tracking so walking translates XYZ. iOS only. */
	void EnsureWorldTrackingARSession();
	void ScheduleWorldTrackingCheck();

	bool bWorldTrackingReady = false;
	int32 WorldTrackingAttempts = 0;
	FTimerHandle WorldTrackingTimer;

	bool bHasSmoothedARRotation = false;
	FRotator SmoothedARRotation = FRotator::ZeroRotator;

	bool bMobileTouchInterfaceReady = false;
	static constexpr int32 MaxInventoryTouchFingers = 10;
	bool InventoryTouchWasDown[MaxInventoryTouchFingers] = {};
};
