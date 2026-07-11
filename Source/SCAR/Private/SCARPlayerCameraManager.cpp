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

	// Keep first-person parameters enabled on mobile so laser/weapon render over AR passthrough.
	if (SCARPhonePreviewParity::ShouldUseMobileCameraPath(GetWorld()))
	{
		OutVT.POV.bUseFirstPersonParameters = true;
		OutVT.POV.FirstPersonScale = 1.f;
	}
	else if (OutVT.POV.FOV <= AdsFovThreshold)
	{
		OutVT.POV.bUseFirstPersonParameters = true;
		OutVT.POV.FirstPersonFOV = AdsFirstPersonFov;
		OutVT.POV.FirstPersonScale = AdsFirstPersonScale;
	}
}
