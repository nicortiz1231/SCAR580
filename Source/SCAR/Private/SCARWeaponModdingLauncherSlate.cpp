#include "SCARWeaponModdingLauncherSlate.h"

#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "GameFramework/PlayerController.h"
#include "SCARWeaponAttachmentBlueprintLibrary.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Text/STextBlock.h"

TSharedPtr<SWidget> FSCARWeaponModdingLauncherSlate::MenuWidget;
TWeakObjectPtr<APlayerController> FSCARWeaponModdingLauncherSlate::OwningController;

void FSCARWeaponModdingLauncherSlate::Show(APlayerController* PlayerController)
{
	if (!PlayerController || !PlayerController->IsLocalController() || !GEngine || !GEngine->GameViewport)
	{
		return;
	}

	if (MenuWidget.IsValid())
	{
		OwningController = PlayerController;
		return;
	}

	OwningController = PlayerController;

	const TSharedRef<SWidget> Overlay = SNew(SOverlay)
		+ SOverlay::Slot()
		.HAlign(HAlign_Left)
		.VAlign(VAlign_Top)
		.Padding(FMargin(18.f, 96.f, 0.f, 0.f))
		[
			SNew(SButton)
			.OnClicked_Lambda([PlayerController]() -> FReply
			{
				USCARWeaponAttachmentBlueprintLibrary::ToggleBodycamWeaponModdingMenu(PlayerController);
				return FReply::Handled();
			})
			[
				SNew(SBorder)
				.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
				.BorderBackgroundColor(FLinearColor(0.86f, 0.45f, 0.05f, 0.96f))
				.Padding(FMargin(18.f, 12.f))
				[
					SNew(STextBlock)
					.Text(FText::FromString(TEXT("Attachments")))
					.Font(FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), 22))
					.ColorAndOpacity(FLinearColor::White)
					.Justification(ETextJustify::Center)
				]
			]
		];

	MenuWidget = Overlay;
	GEngine->GameViewport->AddViewportWidgetContent(Overlay, 100000);
}

void FSCARWeaponModdingLauncherSlate::Hide()
{
	if (MenuWidget.IsValid() && GEngine && GEngine->GameViewport)
	{
		GEngine->GameViewport->RemoveViewportWidgetContent(MenuWidget.ToSharedRef());
	}

	MenuWidget.Reset();
	OwningController.Reset();
}

bool FSCARWeaponModdingLauncherSlate::IsVisible()
{
	return MenuWidget.IsValid();
}
