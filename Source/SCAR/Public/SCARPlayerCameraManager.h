#pragma once

#include "CoreMinimal.h"
#include "Camera/PlayerCameraManager.h"
#include "SCARPlayerCameraManager.generated.h"

/** Forces ultra-low near clip on the final view POV every frame (cannot be bypassed by modifiers). */
UCLASS(NotBlueprintable)
class SCAR_API ASCARPlayerCameraManager : public APlayerCameraManager
{
	GENERATED_BODY()

public:
	ASCARPlayerCameraManager();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|NearClip")
	float ForcedNearClipPlane = 0.0001f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Sniper ADS")
	float AdsFovThreshold = 50.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Sniper ADS")
	float AdsFirstPersonFov = 18.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Sniper ADS")
	float AdsFirstPersonScale = 2.5f;

protected:
	virtual void UpdateViewTargetInternal(FTViewTarget& OutVT, float DeltaTime) override;
};
