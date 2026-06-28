#pragma once

#include "CoreMinimal.h"

bool SCAR_MapImageNormalizedToViewport01_IOS(const FVector2D& ImageNormalized, FVector2D& OutViewport01);
bool SCAR_MapViewport01ToImageNormalized_IOS(const FVector2D& Viewport01, FVector2D& OutImageNormalized);
bool SCAR_GetCameraImageResolution_IOS(FVector2D& OutImageResolution);
