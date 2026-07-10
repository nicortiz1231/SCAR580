#pragma once

#include "CoreMinimal.h"

class UWorld;

namespace SCARPhonePreviewParity
{
	/**
	 * When true, use the same camera path as iOS/Android: main-view FOV only.
	 * Desktop FirstPersonFOV / FirstPersonScale are ignored on mobile and must not
	 * run in editor PIE or preview will not match the device.
	 */
	SCAR_API bool ShouldUseMobileCameraPath(const UWorld* World);
}
