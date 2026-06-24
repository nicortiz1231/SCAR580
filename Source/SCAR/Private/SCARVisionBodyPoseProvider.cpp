#include "SCARVisionBodyPoseProvider.h"

#include "ARBlueprintLibrary.h"
#include "ARTextures.h"
#include "Engine/World.h"
#include "HAL/PlatformTime.h"
#include "SCARVisionBodyPoseBridge.h"

#if PLATFORM_IOS
#include "AppleARKitTextures.h"
#include "AppleImageUtilsTypes.h"
#include "CoreVideo/CoreVideo.h"
#endif

bool USCARVisionBodyPoseProvider::IsSupported() const
{
	return FSCARVisionBodyPoseBridge::IsSupported();
}

void USCARVisionBodyPoseProvider::TickDetection(UWorld* World)
{
	if (!World || !IsSupported())
	{
		return;
	}

	const double NowSeconds = World->GetTimeSeconds();
	const float MinInterval = FMath::Max(DetectionIntervalSeconds, 0.03f);
	if (NowSeconds < NextDetectionTimeSeconds)
	{
		return;
	}

	NextDetectionTimeSeconds = NowSeconds + MinInterval;

	int32 Width = 0;
	int32 Height = 0;
	if (!TryAcquireCameraRgba(World, RgbaBuffer, Width, Height))
	{
		return;
	}

	if (NativeOutput.Num() != FSCARVisionBodyPoseBridge::MaxBodies * FSCARVisionBodyPoseBridge::BodyStride)
	{
		NativeOutput.SetNumZeroed(FSCARVisionBodyPoseBridge::MaxBodies * FSCARVisionBodyPoseBridge::BodyStride);
	}

	const int32 BodyCount = FSCARVisionBodyPoseBridge::DetectFromRgba(
		RgbaBuffer.GetData(),
		Width,
		Height,
		VisionImageOrientation,
		MinJointConfidence,
		NativeOutput,
		MaxBodies,
		FSCARVisionBodyPoseBridge::JointCount);

	PreviousTargets = Targets;
	BuildTargetsFromNative(BodyCount, NowSeconds);
}

bool USCARVisionBodyPoseProvider::TryAcquireCameraRgba(UWorld* World, TArray<uint8>& OutRgba, int32& OutWidth, int32& OutHeight) const
{
#if PLATFORM_IOS
	(void)World;

	UARTexture* CameraTexture = UARBlueprintLibrary::GetARTexture(EARTextureType::CameraImage);
	const UAppleARKitTextureCameraImage* AppleTexture = Cast<UAppleARKitTextureCameraImage>(CameraTexture);
	if (!AppleTexture)
	{
		return false;
	}

	CVPixelBufferRef PixelBuffer = AppleTexture->GetPixelBuffer();
	if (!PixelBuffer)
	{
		return false;
	}

	CVPixelBufferLockBaseAddress(PixelBuffer, kCVPixelBufferLock_ReadOnly);

	const int32 SourceWidth = CVPixelBufferGetWidth(PixelBuffer);
	const int32 SourceHeight = CVPixelBufferGetHeight(PixelBuffer);
	if (SourceWidth <= 0 || SourceHeight <= 0)
	{
		CVPixelBufferUnlockBaseAddress(PixelBuffer, kCVPixelBufferLock_ReadOnly);
		return false;
	}

	const int32 MaxDim = FMath::Max(64, MaxImageDimension);
	const float Scale = static_cast<float>(MaxDim) / static_cast<float>(FMath::Max(SourceWidth, SourceHeight));
	OutWidth = FMath::Max(1, FMath::RoundToInt(SourceWidth * Scale));
	OutHeight = FMath::Max(1, FMath::RoundToInt(SourceHeight * Scale));

	OutRgba.SetNumUninitialized(OutWidth * OutHeight * 4);

	const OSType PixelFormat = CVPixelBufferGetPixelFormatType(PixelBuffer);
	const uint8* BaseAddress = static_cast<const uint8*>(CVPixelBufferGetBaseAddress(PixelBuffer));
	const size_t BytesPerRow = CVPixelBufferGetBytesPerRow(PixelBuffer);

	for (int32 Y = 0; Y < OutHeight; ++Y)
	{
		const int32 SourceY = FMath::Clamp(FMath::RoundToInt((static_cast<float>(Y) + 0.5f) / Scale - 0.5f), 0, SourceHeight - 1);
		for (int32 X = 0; X < OutWidth; ++X)
		{
			const int32 SourceX = FMath::Clamp(FMath::RoundToInt((static_cast<float>(X) + 0.5f) / Scale - 0.5f), 0, SourceWidth - 1);
			const int32 DestIndex = (Y * OutWidth + X) * 4;

			if (PixelFormat == kCVPixelFormatType_32BGRA)
			{
				const uint8* Pixel = BaseAddress + SourceY * BytesPerRow + SourceX * 4;
				OutRgba[DestIndex + 0] = Pixel[2];
				OutRgba[DestIndex + 1] = Pixel[1];
				OutRgba[DestIndex + 2] = Pixel[0];
				OutRgba[DestIndex + 3] = 255;
			}
			else if (PixelFormat == kCVPixelFormatType_32ARGB)
			{
				const uint8* Pixel = BaseAddress + SourceY * BytesPerRow + SourceX * 4;
				OutRgba[DestIndex + 0] = Pixel[1];
				OutRgba[DestIndex + 1] = Pixel[2];
				OutRgba[DestIndex + 2] = Pixel[3];
				OutRgba[DestIndex + 3] = 255;
			}
			else
			{
				OutRgba[DestIndex + 0] = 0;
				OutRgba[DestIndex + 1] = 0;
				OutRgba[DestIndex + 2] = 0;
				OutRgba[DestIndex + 3] = 255;
			}
		}
	}

	CVPixelBufferUnlockBaseAddress(PixelBuffer, kCVPixelBufferLock_ReadOnly);
	return true;
#else
	(void)World;
	(void)OutRgba;
	OutWidth = 0;
	OutHeight = 0;
	return false;
#endif
}

void USCARVisionBodyPoseProvider::BuildTargetsFromNative(const int32 BodyCount, const double NowSeconds)
{
	Targets.Reset();
	TArray<bool> PreviousUsed;
	PreviousUsed.SetNumZeroed(PreviousTargets.Num());

	for (int32 BodyIndex = 0; BodyIndex < BodyCount; ++BodyIndex)
	{
		const int32 Offset = BodyIndex * FSCARVisionBodyPoseBridge::BodyStride;
		if (!NativeOutput.IsValidIndex(Offset + 4))
		{
			continue;
		}

		FSCARScreenSpaceBodyTarget Target;
		Target.MeanConfidence = NativeOutput[Offset];
		Target.Bounds = FVector4(
			NativeOutput[Offset + 1],
			NativeOutput[Offset + 2],
			NativeOutput[Offset + 3],
			NativeOutput[Offset + 4]);

		if (bMirrorViewportX)
		{
			const float MirroredMinX = 1.f - Target.Bounds.Z;
			Target.Bounds.Z = 1.f - Target.Bounds.X;
			Target.Bounds.X = MirroredMinX;
		}

		const FVector2D BoundsCenter(
			(Target.Bounds.X + Target.Bounds.Z) * 0.5f,
			(Target.Bounds.Y + Target.Bounds.W) * 0.5f);
		Target.LocalId = AssociateOrCreateLocalId(BoundsCenter, PreviousUsed);
		Target.LastSeenTimeSeconds = NowSeconds;

		for (int32 JointIndex = 0; JointIndex < FSCARVisionBodyPoseBridge::JointCount; ++JointIndex)
		{
			const int32 JointOffset = Offset + 5 + JointIndex * 3;
			if (!NativeOutput.IsValidIndex(JointOffset + 2))
			{
				continue;
			}

			float X = NativeOutput[JointOffset];
			float Y = NativeOutput[JointOffset + 1];
			const float Confidence = NativeOutput[JointOffset + 2];

			if (bMirrorViewportX && X >= 0.f)
			{
				X = 1.f - X;
			}

			FSCARVisionBodyJoint& Joint = Target.Joints[JointIndex];
			Joint.Confidence = Confidence;
			Joint.bIsValid = X >= 0.f && Y >= 0.f && Confidence >= MinJointConfidence;
			if (Joint.bIsValid)
			{
				// Camera-image normalized coordinates (Vision native, bottom-left origin).
				Joint.NormalizedPosition = FVector2D(X, Y);
			}
		}

		Targets.Add(MoveTemp(Target));
	}
}

int32 USCARVisionBodyPoseProvider::AssociateOrCreateLocalId(
	const FVector2D& BoundsCenter,
	TArray<bool>& PreviousUsed)
{
	int32 BestIndex = INDEX_NONE;
	float BestDistanceSq = MaxAssociationDistance * MaxAssociationDistance;

	for (int32 Index = 0; Index < PreviousTargets.Num(); ++Index)
	{
		if (PreviousUsed.IsValidIndex(Index) && PreviousUsed[Index])
		{
			continue;
		}

		const FSCARScreenSpaceBodyTarget& Previous = PreviousTargets[Index];
		const FVector2D PreviousCenter(
			(Previous.Bounds.X + Previous.Bounds.Z) * 0.5f,
			(Previous.Bounds.Y + Previous.Bounds.W) * 0.5f);
		const float DistanceSq = FVector2D::DistSquared(BoundsCenter, PreviousCenter);
		if (DistanceSq < BestDistanceSq)
		{
			BestDistanceSq = DistanceSq;
			BestIndex = Index;
		}
	}

	if (BestIndex != INDEX_NONE)
	{
		PreviousUsed[BestIndex] = true;
		return PreviousTargets[BestIndex].LocalId;
	}

	return NextLocalId++;
}

FVector2D USCARVisionBodyPoseProvider::NormalizedToViewport01(const FVector2D& VisionNormalized)
{
	return FVector2D(VisionNormalized.X, 1.f - VisionNormalized.Y);
}

FVector2D USCARVisionBodyPoseProvider::ToViewportPosition(const FVector2D& VisionNormalized) const
{
	FVector2D Viewport = NormalizedToViewport01(VisionNormalized);
	if (bMirrorViewportX)
	{
		Viewport.X = 1.f - Viewport.X;
	}

	return Viewport;
}
