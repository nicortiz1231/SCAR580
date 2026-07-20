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
	virtual void OnPossess(APawn* InPawn) override;
	virtual void PlayerTick(float DeltaTime) override;

private:
	UPROPERTY()
	TObjectPtr<USCARARMultiplayerMenuWidget> MultiplayerMenuWidget;

	// BP_FPCharacter has no SCS slot for USCARLocalFirstPersonArmsComponent
	// (it's a marketplace Blueprint asset), so it's attached dynamically here
	// the same way USCARMultiplayerPresentationComponent dynamically creates
	// its opponent pose-driver mesh -- no Blueprint editing required.
	void EnsureLocalFirstPersonArms();

	// Attaches USCARRemoteAvatarAnchorComponent to this controller so remote
	// avatars stay anchored to the real world when the local phone rolls.
	void EnsureRemoteAvatarAnchor();

	// Attaches USCARAvatarWeaponSyncComponent to this controller so remote
	// avatars visibly hold the weapon their player actually has equipped.
	void EnsureAvatarWeaponSync();

	/** Upgrade PoseTracking AR session to World tracking so walking translates XYZ. iOS only. */
	void EnsureWorldTrackingARSession();
	void ScheduleWorldTrackingCheck();

	bool bWorldTrackingReady = false;
	int32 WorldTrackingAttempts = 0;
	FTimerHandle WorldTrackingTimer;

	// FirstPersonCamera drives its rotation via bUsePawnControlRotation (reads
	// ControlRotation), while its bLockToHmd flag independently overrides the
	// camera's own transform straight from the raw ARKit device pose every
	// frame -- completely bypassing ControlRotation. The FPS arms/weapon IK
	// aiming, however, is driven by GetControlRotation(), so without this fix
	// the arms stay aimed wherever ControlRotation last was (effectively
	// fixed to the screen) while the camera itself freely follows the phone.
	// We disable bLockToHmd (done once on BeginPlay) and instead drive
	// ControlRotation directly from a lightly smoothed AR device pose each
	// tick, so the camera and the arm/weapon IK always read the exact same,
	// live, jitter-reduced rotation.
	bool bHasSmoothedARRotation = false;
	FRotator SmoothedARRotation = FRotator::ZeroRotator;
};
