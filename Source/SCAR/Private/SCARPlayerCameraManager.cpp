#include "SCARPlayerCameraManager.h"

#include "CoreGlobals.h"

ASCARPlayerCameraManager::ASCARPlayerCameraManager()
{
}

void ASCARPlayerCameraManager::UpdateViewTargetInternal(FTViewTarget& OutVT, float DeltaTime)
{
	Super::UpdateViewTargetInternal(OutVT, DeltaTime);

	OutVT.POV.PerspectiveNearClipPlane = ForcedNearClipPlane;
	GNearClippingPlane = ForcedNearClipPlane;

	if (OutVT.POV.FOV <= AdsFovThreshold)
	{
		OutVT.POV.bUseFirstPersonParameters = true;
		OutVT.POV.FirstPersonFOV = AdsFirstPersonFov;
		OutVT.POV.FirstPersonScale = AdsFirstPersonScale;
	}
}
