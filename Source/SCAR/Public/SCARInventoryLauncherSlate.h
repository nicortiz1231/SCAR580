#pragma once

#include "CoreMinimal.h"

class APlayerController;
class IInputProcessor;
class SWidget;

class FSCARInventoryLauncherSlate
{
public:
	static void Show(APlayerController* PlayerController);
	static void Hide();
	static bool IsVisible();
	static void RefreshVisibility(APlayerController* PlayerController);

	static APlayerController* GetOwningController();

	/** Returns false if Tab/B already toggled this frame (InputKey + Slate preprocessor). */
	static bool ShouldAcceptToggleHotkey();

	static bool HitTestScreenPoint(
		const FVector2D& ScreenPos,
		const int32 ViewportSizeX,
		const int32 ViewportSizeY);

private:
	static void EnsureHotkeyProcessor();

	static TSharedPtr<SWidget> MenuWidget;
	static TWeakObjectPtr<APlayerController> OwningController;
	static TSharedPtr<IInputProcessor> InputProcessor;
};
