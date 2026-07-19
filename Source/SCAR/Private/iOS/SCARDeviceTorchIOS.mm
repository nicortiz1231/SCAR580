#include "SCARDeviceTorch.h"

#if PLATFORM_IOS

#import <AVFoundation/AVFoundation.h>

DEFINE_LOG_CATEGORY_STATIC(LogSCARDeviceTorch, Log, All);

bool SCARDeviceTorch::IsSupported()
{
	AVCaptureDevice* Device = [AVCaptureDevice defaultDeviceWithMediaType:AVMediaTypeVideo];
	return Device != nil && Device.hasTorch && Device.isTorchAvailable;
}

void SCARDeviceTorch::SetEnabled(bool bEnabled)
{
	// AVCaptureDevice configuration must happen on the main thread.
	dispatch_async(dispatch_get_main_queue(), ^{
		AVCaptureDevice* Device = [AVCaptureDevice defaultDeviceWithMediaType:AVMediaTypeVideo];
		if (Device == nil || !Device.hasTorch)
		{
			UE_LOG(LogSCARDeviceTorch, Warning, TEXT("Device torch unavailable"));
			return;
		}

		NSError* Error = nil;
		if (![Device lockForConfiguration:&Error])
		{
			UE_LOG(
				LogSCARDeviceTorch,
				Warning,
				TEXT("Torch lockForConfiguration failed: %s"),
				Error ? *FString(Error.localizedDescription) : TEXT("(unknown)"));
			return;
		}

		if (bEnabled)
		{
			if (Device.isTorchAvailable && [Device isTorchModeSupported:AVCaptureTorchModeOn])
			{
				NSError* LevelError = nil;
				const BOOL bOk = [Device setTorchModeOnWithLevel:AVCaptureMaxAvailableTorchLevel error:&LevelError];
				if (!bOk)
				{
					// Fallback if level API fails during ARKit session.
					Device.torchMode = AVCaptureTorchModeOn;
					UE_LOG(
						LogSCARDeviceTorch,
						Warning,
						TEXT("setTorchModeOnWithLevel failed (%s); used torchMode=On"),
						LevelError ? *FString(LevelError.localizedDescription) : TEXT("unknown"));
				}
				else
				{
					UE_LOG(LogSCARDeviceTorch, Log, TEXT("iPhone torch ON"));
				}
			}
		}
		else
		{
			if ([Device isTorchModeSupported:AVCaptureTorchModeOff])
			{
				Device.torchMode = AVCaptureTorchModeOff;
				UE_LOG(LogSCARDeviceTorch, Log, TEXT("iPhone torch OFF"));
			}
		}

		[Device unlockForConfiguration];
	});
}

#endif // PLATFORM_IOS
