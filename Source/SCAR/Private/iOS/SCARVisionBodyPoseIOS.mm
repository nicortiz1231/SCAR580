#include "iOS/SCARVisionBodyPoseIOS.h"

#if PLATFORM_IOS
#include "AppleARKitFrame.h"
#include "AppleARKitModule.h"
#include "AppleARKitSystem.h"
#endif

FSCARARKitCameraPixelBufferResult SCAR_TryGetARKitCameraPixelBuffer()
{
	FSCARARKitCameraPixelBufferResult Result;

#if PLATFORM_IOS
	const TSharedPtr<FAppleARKitSystem, ESPMode::ThreadSafe> ArkitSystem = FAppleARKitModule::GetARKitSystem();
	if (!ArkitSystem.IsValid())
	{
		Result.Source = TEXT("no_arkit_sys");
		return Result;
	}

	// Only touch UE-owned CameraImage. Native ARFrame / ARSession pointers are not safe
	// during early session startup and have crashed on device (objc_msgSend SIGSEGV).
	if (void* RawFrame = ArkitSystem->GetGameThreadARFrameRawPointer())
	{
		const FAppleARKitFrame* Frame = static_cast<const FAppleARKitFrame*>(RawFrame);
		if (Frame != nullptr && Frame->CameraImage != nullptr)
		{
			Result.PixelBuffer = Frame->CameraImage;
			Result.Source = TEXT("ue_frame_buf");
			return Result;
		}

		Result.Source = TEXT("ue_frame_empty");
	}
	else
	{
		Result.Source = TEXT("no_ue_frame");
	}
#endif

	return Result;
}
