#include "SCARNearClipCameraModifier.h"

#include "Camera/PlayerCameraManager.h"
#include "CoreGlobals.h"
#include "SCARPhonePreviewParity.h"

USCARNearClipCameraModifier::USCARNearClipCameraModifier()
{
	Priority = 0;
	Alpha = 1.f;
}

bool USCARNearClipCameraModifier::ModifyCamera(float DeltaTime, FMinimalViewInfo& InOutPOV)
{
	Super::ModifyCamera(DeltaTime, InOutPOV);

	// This is what UE actually uses for perspective projection (not GEngine->NearClipPlane).
	InOutPOV.PerspectiveNearClipPlane = NearClipPlane;
	GNearClippingPlane = NearClipPlane;

	const UWorld* ViewWorld = CameraOwner ? CameraOwner->GetWorld() : nullptr;
	if (!SCARPhonePreviewParity::ShouldUseMobileCameraPath(ViewWorld)
		&& InOutPOV.FOV <= AdsFovThreshold)
	{
		InOutPOV.bUseFirstPersonParameters = true;
		InOutPOV.FirstPersonFOV = AdsFirstPersonFov;
		InOutPOV.FirstPersonScale = AdsFirstPersonScale;
	}

	return false;
}
