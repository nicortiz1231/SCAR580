#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "SCARARMultiplayerMenuWidget.generated.h"

class UButton;
class UEditableTextBox;
class UTextBlock;
class APlayerController;

UCLASS()
class SCAR_API USCARARMultiplayerMenuWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	USCARARMultiplayerMenuWidget(const FObjectInitializer& ObjectInitializer);

	void InitializeMenu(class ASCARARMultiplayerPlayerController* InOwningController);
	void InitializeForPlayerController(APlayerController* InPlayerController);
	void SetHostSessionMode(bool bHosting);
	void PresentOnScreen(APlayerController* PlayerController, int32 ZOrder = 10000);

protected:
	virtual void NativeConstruct() override;

private:
	UFUNCTION()
	void HandleHostClicked();

	UFUNCTION()
	void HandleJoinClicked();

	UFUNCTION()
	void HandleDismissClicked();

	void RefreshStatusText();
	void SetStatus(const FString& Message);

	UPROPERTY()
	TObjectPtr<APlayerController> BoundPlayerController;

	UPROPERTY()
	TObjectPtr<class ASCARARMultiplayerPlayerController> OwningController;

	UPROPERTY()
	TObjectPtr<UTextBlock> TitleText;

	UPROPERTY()
	TObjectPtr<UTextBlock> StatusText;

	UPROPERTY()
	TObjectPtr<UTextBlock> HostHintText;

	UPROPERTY()
	TObjectPtr<UEditableTextBox> JoinAddressText;

	UPROPERTY()
	TObjectPtr<UButton> HostButton;

	UPROPERTY()
	TObjectPtr<UButton> JoinButton;

	UPROPERTY()
	TObjectPtr<UButton> DismissButton;
};
