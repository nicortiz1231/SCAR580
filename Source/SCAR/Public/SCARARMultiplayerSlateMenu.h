#pragma once

#include "CoreMinimal.h"

class APlayerController;
class SWidget;

class FSCARARMultiplayerSlateMenu
{
public:
	static void Show(APlayerController* PlayerController);
	static void Hide();
	static bool IsVisible();

private:
	static TSharedPtr<SWidget> MenuWidget;
	static TWeakObjectPtr<APlayerController> OwningController;
};
