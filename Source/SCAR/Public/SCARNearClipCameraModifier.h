#pragma once

#include "CoreMinimal.h"
#include "Camera/CameraModifier.h"
#include "SCARNearClipCameraModifier.generated.h"

/** Forces an ultra-low perspective near clip on every camera update (fixes FP weapon mesh clipping). */
UCLASS(NotBlueprintable)
class SCAR_API USCARNearClipCameraModifier : public UCameraModifier
{
	GENERATED_BODY()

public:
	USCARNearClipCameraModifier();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|NearClip")
	float NearClipPlane = 0.001f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|NearClip")
	float AdsFovThreshold = 50.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|NearClip")
	float AdsFirstPersonFov = 18.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|NearClip")
	float AdsFirstPersonScale = 2.5f;

	virtual bool ModifyCamera(float DeltaTime, FMinimalViewInfo& InOutPOV) override;
};
