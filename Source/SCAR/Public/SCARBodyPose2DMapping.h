#pragma once

#include "CoreMinimal.h"
#include "ARTypes.h"

/** Pose2D screen mapping ported from Unity ARHumanBodyPose2DAlignment / ARHumanBodyDebugOverlay. */
namespace SCARBodyPose2DMapping
{
	bool DetectPose2DNormalized(const FARPose2D& Pose2D);

	/** Unity Pose2DToGui: screen pixels, top-left origin (GUI space). */
	FVector2D Pose2DToGui(
		const FVector2D& RawJoint,
		bool bNormalized,
		bool bFlipPose2DY,
		int32 ScreenWidth,
		int32 ScreenHeight);

	/** Map one Pose2D joint to GUI pixels. Uses image-space letterbox mapping when requested. */
	bool Pose2DJointToGuiPixels(
		const FARPose2D& Pose2D,
		int32 JointIndex,
		int32 ScreenWidth,
		int32 ScreenHeight,
		bool bFlipPose2DY,
		bool bUseImageSpaceMapping,
		FVector2D& OutGuiPixels);
}
