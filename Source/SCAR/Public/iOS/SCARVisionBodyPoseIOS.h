#pragma once

#include "CoreMinimal.h"

struct FSCARARKitCameraPixelBufferResult
{
	void* PixelBuffer = nullptr;
	FString Source = TEXT("none");
};

/** Tries UE frame buffer, native ARFrame, then ARSession.currentFrame.capturedImage. */
FSCARARKitCameraPixelBufferResult SCAR_TryGetARKitCameraPixelBuffer();
