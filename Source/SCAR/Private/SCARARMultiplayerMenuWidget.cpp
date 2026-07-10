#include "SCARARMultiplayerMenuWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/EditableTextBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "GameFramework/PlayerController.h"
#include "SCARARMultiplayerBlueprintLibrary.h"
#include "SCARARMultiplayerPlayerController.h"
#include "Styling/CoreStyle.h"

namespace
{
	FSlateFontInfo MakeMenuFont(const int32 Size, const bool bBold = false)
	{
		FSlateFontInfo Font = FCoreStyle::GetDefaultFontStyle(bBold ? TEXT("Bold") : TEXT("Regular"), Size);
		Font.Size = Size;
		return Font;
	}

	void StyleMenuText(UTextBlock* TextBlock, const int32 FontSize, const bool bBold = false)
	{
		if (!TextBlock)
		{
			return;
		}

		TextBlock->SetFont(MakeMenuFont(FontSize, bBold));
		TextBlock->SetColorAndOpacity(FSlateColor(FLinearColor::White));
		TextBlock->SetShadowOffset(FVector2D(1.f, 1.f));
		TextBlock->SetShadowColorAndOpacity(FLinearColor(0.f, 0.f, 0.f, 0.9f));
	}

	void StyleMenuButton(UButton* Button)
	{
		if (!Button)
		{
			return;
		}

		Button->SetBackgroundColor(FLinearColor(0.12f, 0.45f, 0.95f, 1.f));
	}
}

USCARARMultiplayerMenuWidget::USCARARMultiplayerMenuWidget(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	bIsFocusable = true;
}

void USCARARMultiplayerMenuWidget::PresentOnScreen(APlayerController* PlayerController, const int32 ZOrder)
{
	if (PlayerController)
	{
		SetOwningPlayer(PlayerController);
	}

	if (!IsInViewport())
	{
		AddToViewport(ZOrder);
	}

	SetAnchorsInViewport(FAnchors(0.f, 0.f, 1.f, 1.f));
	SetAlignmentInViewport(FVector2D(0.f, 0.f));
	SetPositionInViewport(FVector2D::ZeroVector);
	SetVisibility(ESlateVisibility::Visible);
	ForceLayoutPrepass();
}

void USCARARMultiplayerMenuWidget::InitializeMenu(ASCARARMultiplayerPlayerController* InOwningController)
{
	OwningController = InOwningController;
	BoundPlayerController = InOwningController;
	RefreshStatusText();
}

void USCARARMultiplayerMenuWidget::InitializeForPlayerController(APlayerController* InPlayerController)
{
	BoundPlayerController = InPlayerController;
	OwningController = Cast<ASCARARMultiplayerPlayerController>(InPlayerController);
	RefreshStatusText();
}

void USCARARMultiplayerMenuWidget::NativeConstruct()
{
	Super::NativeConstruct();

	if (!HostButton && WidgetTree)
	{
		UCanvasPanel* Canvas = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass());
		WidgetTree->RootWidget = Canvas;

		UBorder* Overlay = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
		Overlay->SetBrushColor(FLinearColor(0.f, 0.f, 0.f, 0.82f));
		Overlay->SetPadding(FMargin(48.f));
		if (UCanvasPanelSlot* OverlaySlot = Canvas->AddChildToCanvas(Overlay))
		{
			OverlaySlot->SetAnchors(FAnchors(0.f, 0.f, 1.f, 1.f));
			OverlaySlot->SetOffsets(FMargin(0.f));
		}

		UVerticalBox* RootBox = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
		Overlay->AddChild(RootBox);

		TitleText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
		TitleText->SetText(FText::FromString(TEXT("SCAR AR Multiplayer")));
		TitleText->SetJustification(ETextJustify::Center);
		StyleMenuText(TitleText, 34, true);
		RootBox->AddChild(TitleText);

		StatusText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
		StatusText->SetAutoWrapText(true);
		StatusText->SetJustification(ETextJustify::Center);
		StyleMenuText(StatusText, 20);
		RootBox->AddChild(StatusText);

		HostHintText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
		HostHintText->SetAutoWrapText(true);
		HostHintText->SetJustification(ETextJustify::Center);
		StyleMenuText(HostHintText, 18);
		RootBox->AddChild(HostHintText);

		if (UVerticalBoxSlot* HintSlot = Cast<UVerticalBoxSlot>(HostHintText->Slot))
		{
			HintSlot->SetPadding(FMargin(0.f, 18.f, 0.f, 18.f));
		}

		HostButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
		HostButton->OnClicked.AddDynamic(this, &USCARARMultiplayerMenuWidget::HandleHostClicked);
		StyleMenuButton(HostButton);
		if (UTextBlock* HostLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass()))
		{
			HostLabel->SetText(FText::FromString(TEXT("Host Session (this device)")));
			HostLabel->SetJustification(ETextJustify::Center);
			StyleMenuText(HostLabel, 22, true);
			HostButton->AddChild(HostLabel);
		}
		RootBox->AddChild(HostButton);
		if (UVerticalBoxSlot* HostSlot = Cast<UVerticalBoxSlot>(HostButton->Slot))
		{
			HostSlot->SetPadding(FMargin(0.f, 8.f, 0.f, 8.f));
		}

		JoinAddressText = WidgetTree->ConstructWidget<UEditableTextBox>(UEditableTextBox::StaticClass());
		JoinAddressText->SetHintText(FText::FromString(TEXT("Host IP (e.g. 10.0.0.221)")));
		JoinAddressText->SetText(FText::GetEmpty());
		JoinAddressText->SetIsReadOnly(false);
		if (UVerticalBoxSlot* JoinFieldSlot = Cast<UVerticalBoxSlot>(RootBox->AddChild(JoinAddressText)))
		{
			JoinFieldSlot->SetPadding(FMargin(0.f, 16.f, 0.f, 8.f));
		}

		JoinButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
		JoinButton->OnClicked.AddDynamic(this, &USCARARMultiplayerMenuWidget::HandleJoinClicked);
		StyleMenuButton(JoinButton);
		if (UTextBlock* JoinLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass()))
		{
			JoinLabel->SetText(FText::FromString(TEXT("Join Session")));
			JoinLabel->SetJustification(ETextJustify::Center);
			StyleMenuText(JoinLabel, 22, true);
			JoinButton->AddChild(JoinLabel);
		}
		RootBox->AddChild(JoinButton);

		DismissButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
		DismissButton->OnClicked.AddDynamic(this, &USCARARMultiplayerMenuWidget::HandleDismissClicked);
		StyleMenuButton(DismissButton);
		if (UTextBlock* DismissLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass()))
		{
			DismissLabel->SetText(FText::FromString(TEXT("Hide Menu")));
			DismissLabel->SetJustification(ETextJustify::Center);
			StyleMenuText(DismissLabel, 18);
			DismissButton->AddChild(DismissLabel);
		}
		if (UVerticalBoxSlot* DismissSlot = Cast<UVerticalBoxSlot>(RootBox->AddChild(DismissButton)))
		{
			DismissSlot->SetPadding(FMargin(0.f, 16.f, 0.f, 0.f));
		}
	}

	RefreshStatusText();
}

void USCARARMultiplayerMenuWidget::HandleHostClicked()
{
	if (!BoundPlayerController)
	{
		SetStatus(TEXT("Missing player controller."));
		return;
	}

	SetStatus(TEXT("Starting listen server..."));
	USCARARMultiplayerBlueprintLibrary::HostARMultiplayerSession(BoundPlayerController, TEXT(""));
}

void USCARARMultiplayerMenuWidget::HandleJoinClicked()
{
	if (!BoundPlayerController || !JoinAddressText)
	{
		SetStatus(TEXT("Missing player controller."));
		return;
	}

	const FString Address = JoinAddressText->GetText().ToString().TrimStartAndEnd();
	if (Address.IsEmpty())
	{
		SetStatus(TEXT("Enter the host device IP address."));
		return;
	}

	SetStatus(FString::Printf(TEXT("Connecting to %s..."), *Address));
	const int32 Port = OwningController ? OwningController->DefaultPort : 7777;
	USCARARMultiplayerBlueprintLibrary::JoinARMultiplayerSession(BoundPlayerController, Address, Port);
}

void USCARARMultiplayerMenuWidget::HandleDismissClicked()
{
	SetVisibility(ESlateVisibility::Collapsed);
}

void USCARARMultiplayerMenuWidget::RefreshStatusText()
{
	FString LanIp;
	const bool bHasLanIp = USCARARMultiplayerBlueprintLibrary::GetLocalLanIPv4(LanIp);
	const FString NetMode = USCARARMultiplayerBlueprintLibrary::GetNetModeDescription(this);

	if (HostHintText)
	{
		if (bHasLanIp)
		{
			HostHintText->SetText(FText::FromString(FString::Printf(
				TEXT("Host on this device, then join from the other device using:\n%s:%d"),
				*LanIp,
				OwningController ? OwningController->DefaultPort : 7777)));
		}
		else
		{
			HostHintText->SetText(FText::FromString(
				TEXT("Host on this device. If LAN IP is unavailable, check Wi-Fi in System Settings.")));
		}
	}

	SetStatus(FString::Printf(TEXT("Net mode: %s"), *NetMode));
}

void USCARARMultiplayerMenuWidget::SetHostSessionMode(const bool bHosting)
{
	if (HostButton)
	{
		HostButton->SetVisibility(bHosting ? ESlateVisibility::Collapsed : ESlateVisibility::Visible);
	}

	if (JoinButton)
	{
		JoinButton->SetVisibility(bHosting ? ESlateVisibility::Collapsed : ESlateVisibility::Visible);
	}

	if (JoinAddressText)
	{
		JoinAddressText->SetVisibility(bHosting ? ESlateVisibility::Collapsed : ESlateVisibility::Visible);
	}

	if (bHosting)
	{
		FString LanIp;
		const int32 Port = OwningController ? OwningController->DefaultPort : 7777;
		if (USCARARMultiplayerBlueprintLibrary::GetLocalLanIPv4(LanIp))
		{
			SetStatus(FString::Printf(TEXT("Hosting — tell the other device to join %s:%d"), *LanIp, Port));
		}
		else
		{
			SetStatus(TEXT("Hosting — share this Mac's Wi-Fi IP address with the joining device."));
		}
	}
}

void USCARARMultiplayerMenuWidget::SetStatus(const FString& Message)
{
	if (StatusText)
	{
		StatusText->SetText(FText::FromString(Message));
	}
}
