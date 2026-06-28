#pragma once

#include "CoreMinimal.h"

class APlayerController;

namespace SCARBodyScreenMapping
{
	/** Map normalized camera-image coordinates to viewport UV (0-1, UE top-left origin). */
	bool MapImageNormalizedToViewport01(const FVector2D& ImageNormalized, FVector2D& OutViewport01);

	/** Inverse of MapImageNormalizedToViewport01 for pinning hit feedback to the crosshair. */
	bool MapViewport01ToImageNormalized(const FVector2D& Viewport01, FVector2D& OutImageNormalized);

	/** Map camera-image coordinates to a world point along the view ray at Distance. */
	bool ImageNormalizedToWorldAtDistance(
		APlayerController* PlayerController,
		const FVector2D& ImageNormalized,
		float Distance,
		FVector& OutWorldLocation);

	/** Returns the current AR camera image resolution in pixels when available. */
	bool GetCameraImageResolution(FVector2D& OutImageResolution);
}
