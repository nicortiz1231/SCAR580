#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "SCARInventoryBlueprintLibrary.generated.h"

UCLASS()
class SCAR_API USCARInventoryBlueprintLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "SCAR|Inventory")
	static bool EnsureInventorySystem(class APlayerController* PlayerController);

	/** Every-frame: keep vitals/hotbar hidden; refresh character preview when open. */
	UFUNCTION(BlueprintCallable, Category = "SCAR|Inventory")
	static void TickInventoryPresentation(class APlayerController* PlayerController);

	/** Tab / Inventory button — open or close the backpack pause menu. */
	UFUNCTION(BlueprintCallable, Category = "SCAR|Inventory")
	static bool ToggleInventoryMenu(class APlayerController* PlayerController);

	UFUNCTION(BlueprintPure, Category = "SCAR|Inventory")
	static bool IsInventoryMenuOpen(class APlayerController* PlayerController);
};
