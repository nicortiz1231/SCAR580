#include "SCARARMultiplayerSlateMenu.h"

#include "Engine/Engine.h"
#include "GameFramework/PlayerController.h"
#include "SCARARMultiplayerBlueprintLibrary.h"
#include "SCARARMultiplayerPlayerController.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Text/STextBlock.h"

TSharedPtr<SWidget> FSCARARMultiplayerSlateMenu::MenuWidget;
TWeakObjectPtr<APlayerController> FSCARARMultiplayerSlateMenu::OwningController;

namespace
{
	void RestoreGameplayInput(APlayerController* PlayerController)
	{
		if (!PlayerController)
		{
			return;
		}

		PlayerController->SetShowMouseCursor(false);
		PlayerController->SetInputMode(FInputModeGameOnly());
		PlayerController->bEnableClickEvents = false;
		PlayerController->bEnableMouseOverEvents = false;
	}

	FText MakeJoinHintText()
	{
		FString LanIp;
		const int32 Port = 7777;
		if (USCARARMultiplayerBlueprintLibrary::GetLocalLanIPv4(LanIp))
		{
			return FText::FromString(FString::Printf(
				TEXT("Host on this device, then join from the other device using:\n%s:%d"),
				*LanIp,
				Port));
		}

		return FText::FromString(
			TEXT("Host on this device. Share this Mac's Wi-Fi IP with the joining device."));
	}
}

void FSCARARMultiplayerSlateMenu::Show(APlayerController* PlayerController)
{
	if (!PlayerController || !GEngine || !GEngine->GameViewport)
	{
		return;
	}

	if (UWorld* World = PlayerController->GetWorld())
	{
		if (World->GetNetMode() == NM_Client)
		{
			return;
		}
	}

	if (MenuWidget.IsValid())
	{
		return;
	}

	OwningController = PlayerController;

	TSharedPtr<SEditableTextBox> JoinAddressBox;
	TSharedPtr<STextBlock> StatusText;

	const TSharedRef<SVerticalBox> MenuBox = SNew(SVerticalBox)
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(8.f)
		.HAlign(HAlign_Center)
		[
			SNew(STextBlock)
			.Text(FText::FromString(TEXT("SCAR AR Multiplayer")))
			.Font(FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), 28))
			.Justification(ETextJustify::Center)
		]
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(8.f)
		.HAlign(HAlign_Center)
		[
			SAssignNew(StatusText, STextBlock)
			.Text(FText::FromString(TEXT("Choose host or join.")))
			.Font(FCoreStyle::GetDefaultFontStyle(TEXT("Regular"), 18))
			.Justification(ETextJustify::Center)
			.AutoWrapText(true)
		]
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(16.f, 8.f)
		.HAlign(HAlign_Center)
		[
			SNew(STextBlock)
			.Text_Lambda([]()
			{
				return MakeJoinHintText();
			})
			.Font(FCoreStyle::GetDefaultFontStyle(TEXT("Regular"), 16))
			.Justification(ETextJustify::Center)
			.AutoWrapText(true)
		]
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(8.f)
		.HAlign(HAlign_Center)
		[
			SNew(SBox)
			.MinDesiredWidth(420.f)
			[
				SNew(SButton)
				.HAlign(HAlign_Center)
				.OnClicked_Lambda([StatusText]()
				{
					if (APlayerController* Controller = OwningController.Get())
					{
						if (StatusText.IsValid())
						{
							StatusText->SetText(FText::FromString(TEXT("Starting listen server...")));
						}

						USCARARMultiplayerBlueprintLibrary::HostARMultiplayerSession(Controller, TEXT(""));
						FSCARARMultiplayerSlateMenu::Hide();
					}

					return FReply::Handled();
				})
				[
					SNew(STextBlock)
					.Text(FText::FromString(TEXT("Host Session (this device)")))
					.Font(FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), 20))
					.Justification(ETextJustify::Center)
				]
			]
		]
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(8.f)
		.HAlign(HAlign_Center)
		[
			SAssignNew(JoinAddressBox, SEditableTextBox)
			.MinDesiredWidth(420.f)
			.HintText(FText::FromString(TEXT("Host IP (e.g. 10.0.0.221)")))
		]
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(8.f)
		.HAlign(HAlign_Center)
		[
			SNew(SBox)
			.MinDesiredWidth(420.f)
			[
				SNew(SButton)
				.HAlign(HAlign_Center)
				.OnClicked_Lambda([StatusText, JoinAddressBox]()
				{
					if (!JoinAddressBox.IsValid())
					{
						return FReply::Handled();
					}

					const FString Address = JoinAddressBox->GetText().ToString().TrimStartAndEnd();
					if (Address.IsEmpty())
					{
						if (StatusText.IsValid())
						{
							StatusText->SetText(FText::FromString(TEXT("Enter the host device IP address.")));
						}
						return FReply::Handled();
					}

					if (APlayerController* Controller = OwningController.Get())
					{
						if (StatusText.IsValid())
						{
							StatusText->SetText(FText::FromString(FString::Printf(TEXT("Connecting to %s..."), *Address)));
						}

						const int32 Port = Cast<ASCARARMultiplayerPlayerController>(Controller)
							? Cast<ASCARARMultiplayerPlayerController>(Controller)->DefaultPort
							: 7777;
						USCARARMultiplayerBlueprintLibrary::JoinARMultiplayerSession(Controller, Address, Port);
						FSCARARMultiplayerSlateMenu::Hide();
					}

					return FReply::Handled();
				})
				[
					SNew(STextBlock)
					.Text(FText::FromString(TEXT("Join Session")))
					.Font(FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), 20))
					.Justification(ETextJustify::Center)
				]
			]
		]
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(8.f)
		.HAlign(HAlign_Center)
		[
			SNew(SButton)
			.OnClicked_Lambda([]()
			{
				FSCARARMultiplayerSlateMenu::Hide();
				return FReply::Handled();
			})
			[
				SNew(STextBlock)
				.Text(FText::FromString(TEXT("Hide Menu")))
				.Font(FCoreStyle::GetDefaultFontStyle(TEXT("Regular"), 16))
				.Justification(ETextJustify::Center)
			]
		];

	const TSharedRef<SWidget> Overlay = SNew(SOverlay)
		+ SOverlay::Slot()
		.HAlign(HAlign_Fill)
		.VAlign(VAlign_Fill)
		[
			SNew(SBorder)
			.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
			.BorderBackgroundColor(FLinearColor(0.f, 0.f, 0.f, 0.85f))
			.Padding(FMargin(32.f))
			.HAlign(HAlign_Center)
			.VAlign(VAlign_Center)
			[
				SNew(SBox)
				.MinDesiredWidth(720.f)
				[
					MenuBox
				]
			]
		];

	MenuWidget = Overlay;
	GEngine->GameViewport->AddViewportWidgetContent(Overlay, 20000);

	PlayerController->SetShowMouseCursor(true);
	PlayerController->bEnableClickEvents = true;
	FInputModeGameAndUI InputMode;
	InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
	InputMode.SetHideCursorDuringCapture(false);
	PlayerController->SetInputMode(InputMode);

	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(
			-1,
			6.f,
			FColor::Green,
			TEXT("SCAR multiplayer menu visible (Slate overlay)."));
	}
}

void FSCARARMultiplayerSlateMenu::Hide()
{
	APlayerController* Controller = OwningController.Get();

	if (MenuWidget.IsValid() && GEngine && GEngine->GameViewport)
	{
		GEngine->GameViewport->RemoveViewportWidgetContent(MenuWidget.ToSharedRef());
	}

	MenuWidget.Reset();

	if (!Controller)
	{
		if (GEngine && GEngine->GameViewport)
		{
			if (UWorld* World = GEngine->GameViewport->GetWorld())
			{
				Controller = World->GetFirstPlayerController();
			}
		}
	}

	if (Controller && Controller->IsLocalController())
	{
		RestoreGameplayInput(Controller);
	}

	OwningController.Reset();
}

bool FSCARARMultiplayerSlateMenu::IsVisible()
{
	return MenuWidget.IsValid();
}
