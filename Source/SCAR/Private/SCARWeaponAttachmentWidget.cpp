#include "SCARWeaponAttachmentWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "SCARWeaponAttachmentBlueprintLibrary.h"
#include "Styling/CoreStyle.h"

USCARWeaponAttachmentWidget::USCARWeaponAttachmentWidget(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
}

namespace
{
	FSlateFontInfo MakeAttachmentFont(const int32 Size, const bool bBold = false)
	{
		FSlateFontInfo Font = FCoreStyle::GetDefaultFontStyle(bBold ? TEXT("Bold") : TEXT("Regular"), Size);
		Font.Size = Size;
		return Font;
	}
}

int32 USCARWeaponAttachmentWidget::GetMobileFontSize(const int32 BaseSize) const
{
#if PLATFORM_IOS || PLATFORM_ANDROID
	return BaseSize + 4;
#else
	return BaseSize;
#endif
}

void USCARWeaponAttachmentWidget::InitializeForPawn(APawn* InPawn)
{
	BoundPawn = InPawn;
	RefreshDisplay();
}

void USCARWeaponAttachmentWidget::RefreshDisplay()
{
	RefreshLabels();
}

void USCARWeaponAttachmentWidget::PresentOnScreen(APlayerController* PlayerController, const int32 ZOrder)
{
	if (PlayerController)
	{
		SetOwningPlayer(PlayerController);
	}

	if (!IsInViewport())
	{
		AddToViewport(ZOrder);
	}

	// Top-left, below the status bar — stays clear of mobile fire/ADS touch zones.
	SetAnchorsInViewport(FAnchors(0.f, 0.f, 0.f, 0.f));
	SetAlignmentInViewport(FVector2D(0.f, 0.f));
#if PLATFORM_IOS || PLATFORM_ANDROID
	SetPositionInViewport(FVector2D(16.f, 110.f));
#else
	SetPositionInViewport(FVector2D(16.f, 24.f));
#endif
	SetVisibility(ESlateVisibility::Visible);
	ForceLayoutPrepass();
}

void USCARWeaponAttachmentWidget::NativeConstruct()
{
	Super::NativeConstruct();
	BuildLayoutIfNeeded();
	SetMenuExpanded(false);
	RefreshLabels();
}

void USCARWeaponAttachmentWidget::SetMenuExpanded(const bool bExpanded)
{
	bMenuExpanded = bExpanded;

	if (ExpandedPanel)
	{
		ExpandedPanel->SetVisibility(
			bMenuExpanded ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
	}

	if (MenuToggleButton)
	{
		UTextBlock* ToggleText = Cast<UTextBlock>(MenuToggleButton->GetContent());
		if (ToggleText)
		{
			ToggleText->SetText(FText::FromString(bMenuExpanded ? TEXT("Close Attachments") : TEXT("Attachments")));
		}
	}
}

UButton* USCARWeaponAttachmentWidget::CreateLabeledActionButton(
	UVerticalBox* Parent,
	const FString& ActionLabel,
	TObjectPtr<UTextBlock>& OutStatusLabel,
	const FName HandlerName)
{
	if (!WidgetTree || !Parent)
	{
		return nullptr;
	}

	OutStatusLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
	StyleLabelText(OutStatusLabel, GetMobileFontSize(14));
	Parent->AddChild(OutStatusLabel);

	UButton* Button = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
	StyleCategoryButton(Button);

	UTextBlock* ButtonText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
	ButtonText->SetText(FText::FromString(ActionLabel));
	StyleLabelText(ButtonText, GetMobileFontSize(15), true);
	Button->AddChild(ButtonText);

	if (UVerticalBoxSlot* ButtonSlot = Parent->AddChildToVerticalBox(Button))
	{
		ButtonSlot->SetPadding(FMargin(0.f, 4.f, 0.f, 0.f));
		ButtonSlot->SetSize(FSlateChildSize(ESlateSizeRule::Automatic));
	}

	if (HandlerName == GET_FUNCTION_NAME_CHECKED(USCARWeaponAttachmentWidget, HandleSightClicked))
	{
		Button->OnClicked.AddDynamic(this, &USCARWeaponAttachmentWidget::HandleSightClicked);
	}
	else if (HandlerName == GET_FUNCTION_NAME_CHECKED(USCARWeaponAttachmentWidget, HandleLaserClicked))
	{
		Button->OnClicked.AddDynamic(this, &USCARWeaponAttachmentWidget::HandleLaserClicked);
	}
	else if (HandlerName == GET_FUNCTION_NAME_CHECKED(USCARWeaponAttachmentWidget, HandleMuzzleClicked))
	{
		Button->OnClicked.AddDynamic(this, &USCARWeaponAttachmentWidget::HandleMuzzleClicked);
	}
	else if (HandlerName == GET_FUNCTION_NAME_CHECKED(USCARWeaponAttachmentWidget, HandleGripClicked))
	{
		Button->OnClicked.AddDynamic(this, &USCARWeaponAttachmentWidget::HandleGripClicked);
	}

	return Button;
}

void USCARWeaponAttachmentWidget::BuildLayoutIfNeeded()
{
	if (!WidgetTree || MenuToggleButton)
	{
		return;
	}

	UCanvasPanel* Canvas = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass());
	WidgetTree->RootWidget = Canvas;

	UVerticalBox* RootBox = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	if (UCanvasPanelSlot* RootSlot = Canvas->AddChildToCanvas(RootBox))
	{
		RootSlot->SetAnchors(FAnchors(0.f, 0.f, 0.f, 0.f));
		RootSlot->SetAlignment(FVector2D(0.f, 0.f));
		RootSlot->SetAutoSize(true);
		RootSlot->SetOffsets(FMargin(0.f));
	}

	MenuToggleButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
	MenuToggleButton->SetBackgroundColor(FLinearColor(0.85f, 0.45f, 0.05f, 0.96f));
	MenuToggleButton->OnClicked.AddDynamic(this, &USCARWeaponAttachmentWidget::HandleMenuToggleClicked);

	UTextBlock* ToggleText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
	ToggleText->SetText(FText::FromString(TEXT("Attachments")));
	StyleLabelText(ToggleText, GetMobileFontSize(18), true);
	MenuToggleButton->AddChild(ToggleText);

	if (UVerticalBoxSlot* ToggleSlot = RootBox->AddChildToVerticalBox(MenuToggleButton))
	{
		ToggleSlot->SetPadding(FMargin(0.f));
		ToggleSlot->SetSize(FSlateChildSize(ESlateSizeRule::Automatic));
	}

	ExpandedPanel = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
	ExpandedPanel->SetBrushColor(FLinearColor(0.f, 0.f, 0.f, 0.82f));
	ExpandedPanel->SetPadding(FMargin(12.f));

	UVerticalBox* PanelBox = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	ExpandedPanel->AddChild(PanelBox);

	if (UVerticalBoxSlot* PanelSlot = RootBox->AddChildToVerticalBox(ExpandedPanel))
	{
		PanelSlot->SetPadding(FMargin(0.f, 8.f, 0.f, 0.f));
		PanelSlot->SetSize(FSlateChildSize(ESlateSizeRule::Automatic));
	}

	WeaponText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
	WeaponText->SetAutoWrapText(true);
	StyleLabelText(WeaponText, GetMobileFontSize(13));
	PanelBox->AddChild(WeaponText);

	SightButton = CreateLabeledActionButton(
		PanelBox,
		TEXT("Cycle Sight"),
		SightLabel,
		GET_FUNCTION_NAME_CHECKED(USCARWeaponAttachmentWidget, HandleSightClicked));
	LaserButton = CreateLabeledActionButton(
		PanelBox,
		TEXT("Cycle Laser / Flash"),
		LaserLabel,
		GET_FUNCTION_NAME_CHECKED(USCARWeaponAttachmentWidget, HandleLaserClicked));
	MuzzleButton = CreateLabeledActionButton(
		PanelBox,
		TEXT("Cycle Muzzle / Suppressor"),
		MuzzleLabel,
		GET_FUNCTION_NAME_CHECKED(USCARWeaponAttachmentWidget, HandleMuzzleClicked));
	GripButton = CreateLabeledActionButton(
		PanelBox,
		TEXT("Cycle Grip"),
		GripLabel,
		GET_FUNCTION_NAME_CHECKED(USCARWeaponAttachmentWidget, HandleGripClicked));
}

void USCARWeaponAttachmentWidget::RefreshLabels()
{
	const bool bSupported = USCARWeaponAttachmentBlueprintLibrary::SupportsWeaponAttachments(BoundPawn.Get());
	const ESlateVisibility RowVisibility = bSupported ? ESlateVisibility::Visible : ESlateVisibility::Collapsed;

	if (WeaponText)
	{
		WeaponText->SetText(
			bSupported
				? FText::FromString(TEXT("Tap a button to change the equipped weapon attachment."))
				: FText::FromString(TEXT("Equip a rifle, pistol, or sniper to modify attachments.")));
		WeaponText->SetVisibility(
			bMenuExpanded ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
	}

	if (SightLabel)
	{
		SightLabel->SetText(BuildButtonLabel(ESCARWeaponAttachmentCategory::Sight));
		SightLabel->SetVisibility(RowVisibility);
	}
	if (LaserLabel)
	{
		LaserLabel->SetText(BuildButtonLabel(ESCARWeaponAttachmentCategory::Laser));
		LaserLabel->SetVisibility(RowVisibility);
	}
	if (MuzzleLabel)
	{
		MuzzleLabel->SetText(BuildButtonLabel(ESCARWeaponAttachmentCategory::Muzzle));
		MuzzleLabel->SetVisibility(RowVisibility);
	}
	if (GripLabel)
	{
		GripLabel->SetText(BuildButtonLabel(ESCARWeaponAttachmentCategory::Grip));
		GripLabel->SetVisibility(RowVisibility);
	}

	if (SightButton)
	{
		SightButton->SetVisibility(RowVisibility);
	}
	if (LaserButton)
	{
		LaserButton->SetVisibility(RowVisibility);
	}
	if (MuzzleButton)
	{
		MuzzleButton->SetVisibility(RowVisibility);
	}
	if (GripButton)
	{
		GripButton->SetVisibility(RowVisibility);
	}
}

FText USCARWeaponAttachmentWidget::BuildButtonLabel(const ESCARWeaponAttachmentCategory Category) const
{
	switch (Category)
	{
	case ESCARWeaponAttachmentCategory::Sight:
		return FText::Format(
			NSLOCTEXT("SCAR", "SightAttachmentLabel", "Sight: {0}"),
			USCARWeaponAttachmentBlueprintLibrary::GetEquippedWeaponAttachmentLabel(BoundPawn.Get(), Category));
	case ESCARWeaponAttachmentCategory::Laser:
		return FText::Format(
			NSLOCTEXT("SCAR", "LaserAttachmentLabel", "Laser / Flash: {0}"),
			USCARWeaponAttachmentBlueprintLibrary::GetEquippedWeaponAttachmentLabel(BoundPawn.Get(), Category));
	case ESCARWeaponAttachmentCategory::Muzzle:
		return FText::Format(
			NSLOCTEXT("SCAR", "MuzzleAttachmentLabel", "Muzzle / Suppressor: {0}"),
			USCARWeaponAttachmentBlueprintLibrary::GetEquippedWeaponAttachmentLabel(BoundPawn.Get(), Category));
	case ESCARWeaponAttachmentCategory::Grip:
	default:
		return FText::Format(
			NSLOCTEXT("SCAR", "GripAttachmentLabel", "Grip: {0}"),
			USCARWeaponAttachmentBlueprintLibrary::GetEquippedWeaponAttachmentLabel(BoundPawn.Get(), Category));
	}
}

void USCARWeaponAttachmentWidget::StyleCategoryButton(UButton* Button) const
{
	if (!Button)
	{
		return;
	}

	Button->SetBackgroundColor(FLinearColor(0.1f, 0.42f, 0.82f, 0.96f));
}

void USCARWeaponAttachmentWidget::StyleLabelText(
	UTextBlock* TextBlock,
	const int32 FontSize,
	const bool bBold) const
{
	if (!TextBlock)
	{
		return;
	}

	TextBlock->SetFont(MakeAttachmentFont(FontSize, bBold));
	TextBlock->SetColorAndOpacity(FSlateColor(FLinearColor::White));
	TextBlock->SetShadowOffset(FVector2D(1.f, 1.f));
	TextBlock->SetShadowColorAndOpacity(FLinearColor(0.f, 0.f, 0.f, 0.85f));
}

void USCARWeaponAttachmentWidget::HandleMenuToggleClicked()
{
	SetMenuExpanded(!bMenuExpanded);
	RefreshLabels();
}

void USCARWeaponAttachmentWidget::HandleSightClicked()
{
	USCARWeaponAttachmentBlueprintLibrary::CycleEquippedWeaponAttachment(
		BoundPawn.Get(),
		ESCARWeaponAttachmentCategory::Sight);
	RefreshLabels();
}

void USCARWeaponAttachmentWidget::HandleLaserClicked()
{
	USCARWeaponAttachmentBlueprintLibrary::CycleEquippedWeaponAttachment(
		BoundPawn.Get(),
		ESCARWeaponAttachmentCategory::Laser);
	RefreshLabels();
}

void USCARWeaponAttachmentWidget::HandleMuzzleClicked()
{
	USCARWeaponAttachmentBlueprintLibrary::CycleEquippedWeaponAttachment(
		BoundPawn.Get(),
		ESCARWeaponAttachmentCategory::Muzzle);
	RefreshLabels();
}

void USCARWeaponAttachmentWidget::HandleGripClicked()
{
	USCARWeaponAttachmentBlueprintLibrary::CycleEquippedWeaponAttachment(
		BoundPawn.Get(),
		ESCARWeaponAttachmentCategory::Grip);
	RefreshLabels();
}
