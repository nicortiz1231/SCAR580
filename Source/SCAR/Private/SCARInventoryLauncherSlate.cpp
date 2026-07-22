#include "SCARInventoryLauncherSlate.h"

#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "Framework/Application/IInputProcessor.h"
#include "Framework/Application/SlateApplication.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"
#include "SCARInventoryBlueprintLibrary.h"
#include "Styling/CoreStyle.h"
#include "TimerManager.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Text/STextBlock.h"

TSharedPtr<SWidget> FSCARInventoryLauncherSlate::MenuWidget;
TWeakObjectPtr<APlayerController> FSCARInventoryLauncherSlate::OwningController;
TSharedPtr<IInputProcessor> FSCARInventoryLauncherSlate::InputProcessor;

namespace
{
	/**
	 * Catches Tab/B before Slate focus-navigation consumes them while the
	 * inventory overlay uses GameAndUI input mode.
	 */
	class FSCARInventoryHotkeyProcessor final : public IInputProcessor
	{
	public:
		virtual void Tick(const float /*DeltaTime*/, FSlateApplication& /*SlateApp*/, TSharedRef<ICursor> /*Cursor*/) override
		{
		}

		virtual bool HandleKeyDownEvent(FSlateApplication& /*SlateApp*/, const FKeyEvent& InKeyEvent) override
		{
			if (InKeyEvent.IsRepeat())
			{
				return false;
			}

			const FKey Key = InKeyEvent.GetKey();
			if (Key != EKeys::Tab && Key != EKeys::B)
			{
				return false;
			}

			APlayerController* PC = FSCARInventoryLauncherSlate::GetOwningController();
			if (!PC || !PC->IsLocalController())
			{
				return false;
			}

			USCARInventoryBlueprintLibrary::ToggleInventoryMenu(PC);
			return true;
		}
	};

	double GLastInventoryToggleSeconds = 0.0;
}

APlayerController* FSCARInventoryLauncherSlate::GetOwningController()
{
	return OwningController.Get();
}

bool FSCARInventoryLauncherSlate::ShouldAcceptToggleHotkey()
{
	const double Now = FPlatformTime::Seconds();
	// InputKey and the Slate preprocessor can both see the same press.
	if (Now - GLastInventoryToggleSeconds < 0.12)
	{
		return false;
	}

	GLastInventoryToggleSeconds = Now;
	return true;
}

void FSCARInventoryLauncherSlate::EnsureHotkeyProcessor()
{
	if (InputProcessor.IsValid() || !FSlateApplication::IsInitialized())
	{
		return;
	}

	InputProcessor = MakeShared<FSCARInventoryHotkeyProcessor>();
	FSlateApplication::Get().RegisterInputPreProcessor(InputProcessor, 0);
}

void FSCARInventoryLauncherSlate::Show(APlayerController* PlayerController)
{
	if (!PlayerController || !PlayerController->IsLocalController() || !GEngine || !GEngine->GameViewport)
	{
		return;
	}

	OwningController = PlayerController;
	EnsureHotkeyProcessor();

	// Slate buttons need touch/click enabled on mobile — GameOnly blocks them otherwise.
	PlayerController->bEnableClickEvents = true;
	PlayerController->bEnableTouchEvents = true;

	// Defer inventory HUD setup one tick so BeginPlay Blueprint Setup isn't mid-flight.
	if (UWorld* World = PlayerController->GetWorld())
	{
		TWeakObjectPtr<APlayerController> WeakPC(PlayerController);
		World->GetTimerManager().SetTimerForNextTick(FTimerDelegate::CreateLambda([WeakPC]()
		{
			if (APlayerController* PC = WeakPC.Get())
			{
				USCARInventoryBlueprintLibrary::EnsureInventorySystem(PC);
			}
		}));
	}

	if (MenuWidget.IsValid())
	{
		return;
	}

	const TSharedRef<SWidget> Overlay = SNew(SOverlay)
		+ SOverlay::Slot()
		.HAlign(HAlign_Right)
		.VAlign(VAlign_Top)
		.Padding(FMargin(0.f, 18.f, 18.f, 0.f))
		[
			SNew(SButton)
			.OnClicked_Lambda([PlayerController]() -> FReply
			{
				USCARInventoryBlueprintLibrary::ToggleInventoryMenu(PlayerController);
				return FReply::Handled();
			})
			[
				SNew(SBorder)
				.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
				.BorderBackgroundColor(FLinearColor(0.08f, 0.16f, 0.28f, 0.96f))
				.Padding(FMargin(18.f, 12.f))
				[
					SNew(STextBlock)
					.Text(FText::FromString(TEXT("Inventory")))
					.Font(FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), 22))
					.ColorAndOpacity(FLinearColor::White)
					.Justification(ETextJustify::Center)
				]
			]
		];

	MenuWidget = Overlay;
	GEngine->GameViewport->AddViewportWidgetContent(Overlay, 100001);
}

void FSCARInventoryLauncherSlate::Hide()
{
	if (MenuWidget.IsValid() && GEngine && GEngine->GameViewport)
	{
		GEngine->GameViewport->RemoveViewportWidgetContent(MenuWidget.ToSharedRef());
	}

	MenuWidget.Reset();
	OwningController.Reset();

	if (InputProcessor.IsValid() && FSlateApplication::IsInitialized())
	{
		FSlateApplication::Get().UnregisterInputPreProcessor(InputProcessor);
	}
	InputProcessor.Reset();
}

bool FSCARInventoryLauncherSlate::IsVisible()
{
	return MenuWidget.IsValid();
}

void FSCARInventoryLauncherSlate::RefreshVisibility(APlayerController* PlayerController)
{
	if (!MenuWidget.IsValid())
	{
		return;
	}

	if (USCARInventoryBlueprintLibrary::IsInventoryMenuOpen(PlayerController))
	{
		// Keep the launcher visible so players can close the menu from the same button.
	}
}

bool FSCARInventoryLauncherSlate::HitTestScreenPoint(
	const FVector2D& ScreenPos,
	const int32 ViewportSizeX,
	const int32 ViewportSizeY)
{
	if (ViewportSizeX <= 0 || ViewportSizeY <= 0)
	{
		return false;
	}

	auto InLauncherRegion = [](const float NormX, const float NormY) -> bool
	{
		// Top-right Inventory launcher (generous bounds for notches / DPI variance).
		return NormX >= 0.50f && NormX <= 1.05f && NormY >= 0.f && NormY <= 0.22f;
	};

	const float PixelNormX = ScreenPos.X / static_cast<float>(ViewportSizeX);
	const float PixelNormY = ScreenPos.Y / static_cast<float>(ViewportSizeY);
	if (InLauncherRegion(PixelNormX, PixelNormY))
	{
		return true;
	}

	// Some mobile paths report normalized 0-1 coordinates instead of pixels.
	if (ScreenPos.X >= 0.f && ScreenPos.X <= 1.5f && ScreenPos.Y >= 0.f && ScreenPos.Y <= 1.5f)
	{
		return InLauncherRegion(ScreenPos.X, ScreenPos.Y);
	}

	return false;
}
