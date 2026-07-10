#include "SCARPlayerCameraManager.h"

#include "CoreGlobals.h"
#include "SCARPhonePreviewParity.h"

ASCARPlayerCameraManager::ASCARPlayerCameraManager()
{
}

void ASCARPlayerCameraManager::UpdateViewTargetInternal(FTViewTarget& OutVT, float DeltaTime)
{
	Super::UpdateViewTargetInternal(OutVT, DeltaTime);

	OutVT.POV.PerspectiveNearClipPlane = ForcedNearClipPlane;
	GNearClippingPlane = ForcedNearClipPlane;

	// Mobile (and editor PIE mirroring phone) ignore FirstPersonFOV/Scale — main FOV only.
	if (SCARPhonePreviewParity::ShouldUseMobileCameraPath(GetWorld()))
	{
		OutVT.POV.bUseFirstPersonParameters = false;
	}
	else if (OutVT.POV.FOV <= AdsFovThreshold)
	{
		OutVT.POV.bUseFirstPersonParameters = true;
		OutVT.POV.FirstPersonFOV = AdsFirstPersonFov;
		OutVT.POV.FirstPersonScale = AdsFirstPersonScale;
	}
}
