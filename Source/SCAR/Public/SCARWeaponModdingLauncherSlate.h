#pragma once

#include "Widgets/SWidget.h"

class APlayerController;
class SWidget;

/** Always-visible mobile launcher that opens Bodycam UI_WeaponModding. */
class FSCARWeaponModdingLauncherSlate
{
public:
	static void Show(APlayerController* PlayerController);
	static void Hide();
	static bool IsVisible();

private:
	static TSharedPtr<SWidget> MenuWidget;
	static TWeakObjectPtr<APlayerController> OwningController;
};
