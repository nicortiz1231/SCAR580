#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "SCARWeaponAttachmentTypes.h"
#include "SCARWeaponAttachmentWidget.generated.h"

class UBorder;
class UButton;
class UTextBlock;
class UVerticalBox;
class APawn;

UCLASS()
class SCAR_API USCARWeaponAttachmentWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	USCARWeaponAttachmentWidget(const FObjectInitializer& ObjectInitializer);

	void InitializeForPawn(APawn* InPawn);
	void PresentOnScreen(class APlayerController* PlayerController, int32 ZOrder = 50000);
	void RefreshDisplay();

protected:
	virtual void NativeConstruct() override;

private:
	UFUNCTION()
	void HandleMenuToggleClicked();

	UFUNCTION()
	void HandleSightClicked();

	UFUNCTION()
	void HandleLaserClicked();

	UFUNCTION()
	void HandleMuzzleClicked();

	UFUNCTION()
	void HandleGripClicked();

	void BuildLayoutIfNeeded();
	void RefreshLabels();
	void SetMenuExpanded(bool bExpanded);
	FText BuildButtonLabel(ESCARWeaponAttachmentCategory Category) const;
	int32 GetMobileFontSize(const int32 BaseSize) const;
	void StyleCategoryButton(UButton* Button) const;
	void StyleLabelText(UTextBlock* TextBlock, const int32 FontSize, const bool bBold = false) const;
	UButton* CreateLabeledActionButton(
		UVerticalBox* Parent,
		const FString& ActionLabel,
		TObjectPtr<UTextBlock>& OutStatusLabel,
		const FName HandlerName);

	UPROPERTY()
	TObjectPtr<APawn> BoundPawn;

	UPROPERTY()
	TObjectPtr<UButton> MenuToggleButton;

	UPROPERTY()
	TObjectPtr<UBorder> ExpandedPanel;

	UPROPERTY()
	TObjectPtr<UTextBlock> WeaponText;

	UPROPERTY()
	TObjectPtr<UButton> SightButton;

	UPROPERTY()
	TObjectPtr<UButton> LaserButton;

	UPROPERTY()
	TObjectPtr<UButton> MuzzleButton;

	UPROPERTY()
	TObjectPtr<UButton> GripButton;

	UPROPERTY()
	TObjectPtr<UTextBlock> SightLabel;

	UPROPERTY()
	TObjectPtr<UTextBlock> LaserLabel;

	UPROPERTY()
	TObjectPtr<UTextBlock> MuzzleLabel;

	UPROPERTY()
	TObjectPtr<UTextBlock> GripLabel;

	bool bMenuExpanded = false;
};
