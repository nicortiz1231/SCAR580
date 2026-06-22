#include "SCARBodyPose2DMapping.h"

#include "SCARBodyScreenMapping.h"

namespace SCARBodyPose2DMapping
{
	bool DetectPose2DNormalized(const FARPose2D& Pose2D)
	{
		float MaxX = 0.f;
		float MaxY = 0.f;
		for (int32 Index = 0; Index < Pose2D.JointLocations.Num(); ++Index)
		{
			if (!Pose2D.IsJointTracked.IsValidIndex(Index) || !Pose2D.IsJointTracked[Index])
			{
				continue;
			}

			MaxX = FMath::Max(MaxX, Pose2D.JointLocations[Index].X);
			MaxY = FMath::Max(MaxY, Pose2D.JointLocations[Index].Y);
		}

		return MaxX <= 1.5f && MaxY <= 1.5f;
	}

	FVector2D Pose2DToGui(
		const FVector2D& RawJoint,
		const bool bNormalized,
		const bool bFlipPose2DY,
		const int32 ScreenWidth,
		const int32 ScreenHeight)
	{
		const float ScreenW = static_cast<float>(FMath::Max(ScreenWidth, 1));
		const float ScreenH = static_cast<float>(FMath::Max(ScreenHeight, 1));

		float X = bNormalized ? RawJoint.X * ScreenW : RawJoint.X;
		float Y = bNormalized ? RawJoint.Y * ScreenH : RawJoint.Y;
		if (bFlipPose2DY)
		{
			Y = ScreenH - Y;
		}

		return FVector2D(X, Y);
	}

	bool Pose2DJointToGuiPixels(
		const FARPose2D& Pose2D,
		const int32 JointIndex,
		const int32 ScreenWidth,
		const int32 ScreenHeight,
		const bool bFlipPose2DY,
		const bool bUseImageSpaceMapping,
		FVector2D& OutGuiPixels)
	{
		if (!Pose2D.JointLocations.IsValidIndex(JointIndex))
		{
			return false;
		}

		const FVector2D Raw = Pose2D.JointLocations[JointIndex];
		const bool bNormalized = DetectPose2DNormalized(Pose2D);

		if (bUseImageSpaceMapping)
		{
			FVector2D ImageUV;
			if (bNormalized)
			{
				ImageUV = Raw;
			}
			else
			{
				FVector2D ImageResolution(1920.f, 1440.f);
				SCARBodyScreenMapping::GetCameraImageResolution(ImageResolution);
				ImageUV = FVector2D(
					Raw.X / FMath::Max(ImageResolution.X, 1.f),
					Raw.Y / FMath::Max(ImageResolution.Y, 1.f));
			}

			FVector2D Viewport01;
			if (!SCARBodyScreenMapping::MapImageNormalizedToViewport01(ImageUV, Viewport01))
			{
				return false;
			}

			OutGuiPixels = FVector2D(
				Viewport01.X * ScreenWidth,
				Viewport01.Y * ScreenHeight);
			return true;
		}

		OutGuiPixels = Pose2DToGui(Raw, bNormalized, bFlipPose2DY, ScreenWidth, ScreenHeight);
		return true;
	}
}
