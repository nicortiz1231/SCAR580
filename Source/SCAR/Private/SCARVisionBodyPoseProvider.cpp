#include "SCARVisionBodyPoseProvider.h"

#include "ARBlueprintLibrary.h"
#include "ARTextures.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "HAL/PlatformTime.h"
#include "SCARVisionBodyPoseBridge.h"

#if PLATFORM_IOS
#include "AppleARKitTextures.h"
#include "AppleImageUtilsTypes.h"
#include "CoreVideo/CoreVideo.h"
#include "iOS/SCARVisionBodyPoseIOS.h"
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

	const double NowWorldSeconds = World->GetTimeSeconds();
	const float MinInterval = FMath::Max(DetectionIntervalSeconds, 0.03f);
	if (NowWorldSeconds < NextDetectionTimeSeconds)
	{
		return;
	}

	NextDetectionTimeSeconds = NowWorldSeconds + MinInterval;

	const double DetectedAtSeconds = FPlatformTime::Seconds();
	PreviousTargets = Targets;

	int32 BodyCount = 0;
	const bool bHadCamera = TryRunDetectionFromCamera(World, BodyCount);

	if (bHadCamera && BodyCount > 0)
	{
		BuildTargetsFromNative(BodyCount, DetectedAtSeconds);
	}
	else
	{
		PruneStaleTargets(DetectedAtSeconds, 0.35);
	}
}

int32 USCARVisionBodyPoseProvider::RunVisionOnPixelBuffer(void* PixelBuffer)
{
#if PLATFORM_IOS
	if (!PixelBuffer)
	{
		return 0;
	}

	if (NativeOutput.Num() != FSCARVisionBodyPoseBridge::MaxBodies * FSCARVisionBodyPoseBridge::BodyStride)
	{
		NativeOutput.SetNumZeroed(FSCARVisionBodyPoseBridge::MaxBodies * FSCARVisionBodyPoseBridge::BodyStride);
	}

	const int32 MaxDim = FMath::Max(64, MaxImageDimension);

	auto RunAtOrientation = [this, PixelBuffer, MaxDim](const int32 Orientation) -> int32
	{
		int32 Count = FSCARVisionBodyPoseBridge::DetectFromPixelBufferDownscaled(
			PixelBuffer,
			MaxDim,
			Orientation,
			MinJointConfidence,
			NativeOutput,
			MaxBodies,
			FSCARVisionBodyPoseBridge::JointCount);

		if (Count == 0)
		{
			Count = FSCARVisionBodyPoseBridge::DetectFromPixelBuffer(
				PixelBuffer,
				Orientation,
				MinJointConfidence,
				NativeOutput,
				MaxBodies,
				FSCARVisionBodyPoseBridge::JointCount);
		}

		return Count;
	};

	int32 Orientation = FMath::Clamp(VisionImageOrientation, 1, 8);
	if (bAutoDetectOrientation)
	{
		Orientation = FMath::Clamp(CachedAutoOrientation, 1, 8);
	}

	int32 BodyCount = RunAtOrientation(Orientation);

	if (BodyCount == 0 && bAutoDetectOrientation)
	{
		int32 BestCount = 0;
		int32 BestOrientation = Orientation;
		for (int32 Candidate = 1; Candidate <= 8; ++Candidate)
		{
			if (Candidate == Orientation)
			{
				continue;
			}

			const int32 CandidateCount = RunAtOrientation(Candidate);
			if (CandidateCount > BestCount)
			{
				BestCount = CandidateCount;
				BestOrientation = Candidate;
			}
		}

		if (BestCount > 0)
		{
			CachedAutoOrientation = BestOrientation;
			Orientation = BestOrientation;
			BodyCount = BestCount;
		}
	}

	DebugLastOrientation = Orientation;
	return BodyCount;
#else
	(void)PixelBuffer;
	return 0;
#endif
}

bool USCARVisionBodyPoseProvider::TryRunDetectionFromCamera(UWorld* World, int32& OutBodyCount)
{
	OutBodyCount = 0;
	DebugLastCameraSource = TEXT("none");
	bDebugHadCameraBuffer = false;
#if PLATFORM_IOS
	(void)World;

	CVPixelBufferRef PixelBuffer = nullptr;
	FString Source = TEXT("none");

	// Prefer UE's AR texture wrapper — avoids raw ARSession / ARFrame pointers that can
	// be stale during session startup and crash inside objc_msgSend on device.
	if (UARTexture* CameraTexture = UARBlueprintLibrary::GetARTexture(EARTextureType::CameraImage))
	{
		if (const IAppleImageInterface* AppleImage = Cast<IAppleImageInterface>(CameraTexture))
		{
			PixelBuffer = AppleImage->GetPixelBuffer();
			if (PixelBuffer)
			{
				Source = TEXT("apple_iface");
			}
		}

		if (!PixelBuffer)
		{
			if (const UAppleARKitTextureCameraImage* AppleTexture = Cast<UAppleARKitTextureCameraImage>(CameraTexture))
			{
				PixelBuffer = AppleTexture->GetPixelBuffer();
				if (PixelBuffer)
				{
					Source = TEXT("ar_texture");
				}
			}
		}

		if (!PixelBuffer)
		{
			Source = FString::Printf(TEXT("tex_%s"), *CameraTexture->GetClass()->GetName());
		}
	}

	if (!PixelBuffer)
	{
		const FSCARARKitCameraPixelBufferResult ArkitResult = SCAR_TryGetARKitCameraPixelBuffer();
		if (ArkitResult.PixelBuffer)
		{
			PixelBuffer = static_cast<CVPixelBufferRef>(ArkitResult.PixelBuffer);
			Source = ArkitResult.Source;
		}
		else
		{
			Source = ArkitResult.Source.IsEmpty() ? TEXT("no_texture") : ArkitResult.Source;
		}
	}

	DebugLastCameraSource = Source;
	bDebugHadCameraBuffer = PixelBuffer != nullptr;
	if (!PixelBuffer)
	{
		DebugLastBodyCount = 0;
		return false;
	}

	OutBodyCount = RunVisionOnPixelBuffer(PixelBuffer);
	DebugLastBodyCount = OutBodyCount;
	return true;
#else
	(void)World;
	return false;
#endif
}

void USCARVisionBodyPoseProvider::PruneStaleTargets(const double NowSeconds, const float MaxAgeSeconds)
{
	Targets.RemoveAll([NowSeconds, MaxAgeSeconds](const FSCARScreenSpaceBodyTarget& Target)
	{
		return NowSeconds - Target.LastSeenTimeSeconds > MaxAgeSeconds;
	});
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
				// Unity ARScreenSpaceBodyTarget: normalized viewport, bottom-left origin.
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
	// Vision / Unity viewport bottom-left -> UE screen top-left.
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
