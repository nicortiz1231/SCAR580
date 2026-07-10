#include "SCARPhonePreviewParity.h"

#include "Engine/World.h"

namespace SCARPhonePreviewParity
{
bool ShouldUseMobileCameraPath(const UWorld* World)
{
#if PLATFORM_IOS || PLATFORM_ANDROID
	return true;
#else
#if WITH_EDITOR
	if (World && World->IsPlayInEditor())
	{
		return true;
	}
#endif
	return false;
#endif
}
} // namespace SCARPhonePreviewParity
