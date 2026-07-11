#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "SCARWeaponAttachmentTypes.h"
#include "SCARWeaponAttachmentBlueprintLibrary.generated.h"

UCLASS()
class SCAR_API USCARWeaponAttachmentBlueprintLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "SCAR|Attachments")
	static bool ToggleBodycamWeaponModdingMenu(class APlayerController* PlayerController);

	/** Scales the Bodycam attachment menu to fit portrait phone screens. */
	UFUNCTION(BlueprintCallable, Category = "SCAR|Attachments")
	static void ApplyWeaponModdingPortraitLayout(
		class UUserWidget* ModdingWidget,
		class APlayerController* PlayerController);

	UFUNCTION(BlueprintCallable, Category = "SCAR|Attachments")
	static bool SupportsWeaponAttachments(class APawn* Pawn);

	UFUNCTION(BlueprintCallable, Category = "SCAR|Attachments")
	static bool CycleEquippedWeaponAttachment(class APawn* Pawn, ESCARWeaponAttachmentCategory Category);

	UFUNCTION(BlueprintCallable, Category = "SCAR|Attachments")
	static FText GetEquippedWeaponAttachmentLabel(class APawn* Pawn, ESCARWeaponAttachmentCategory Category);

	UFUNCTION(BlueprintCallable, Category = "SCAR|Attachments")
	static void RefreshEquippedWeaponAttachments(class APawn* Pawn);

	/** Re-spawns attachments on the equipped weapon without copying slot data (for UI_WeaponModding). */
	UFUNCTION(BlueprintCallable, Category = "SCAR|Attachments")
	static void ApplySpawnedWeaponAttachments(class APawn* Pawn);

	/** Makes Bodycam laser mesh, beam, decal, and flashlight visible in AR passthrough. */
	UFUNCTION(BlueprintCallable, Category = "SCAR|Attachments")
	static void EnsureWeaponLaserFlashEffectsForPawn(class APawn* Pawn);

	UFUNCTION(BlueprintCallable, Category = "SCAR|Attachments")
	static void EnsureWeaponLaserFlashEffects(class AActor* Weapon);
};
