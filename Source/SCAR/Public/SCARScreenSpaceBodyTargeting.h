#pragma once

#include "CoreMinimal.h"
#include "SCARBodyDetectionTypes.h"
#include "SCARBodyCombatTypes.h"

struct FARPose2D;
class APlayerController;

/** Screen-space body aim tests ported from Unity ARScreenSpaceBodyTarget / ARScreenSpaceTargetResolver. */
namespace SCARScreenSpaceBodyTargeting
{
	struct FSCARScreenSpaceAimSample
	{
		int32 TargetId = INDEX_NONE;
		TArray<FVector2D> JointViewport01;
		TArray<FVector2D> JointImageUV;
		TArray<bool> JointValid;
		FVector4 BoundsViewport01 = FVector4(0.f, 0.f, 1.f, 1.f);
		double LastSeenTimeSeconds = 0.0;
	};

	bool BuildVisionAimSample(const FSCARScreenSpaceBodyTarget& Target, FSCARScreenSpaceAimSample& OutSample);
	bool BuildPose2DAimSample(
		const FARPose2D& Pose2D,
		APlayerController* PlayerController,
		bool bFlipPose2DY,
		bool bUseImageSpaceMapping,
		int32 TargetId,
		FSCARScreenSpaceAimSample& OutSample);

	bool TryGetBestTarget(
		const TArray<FSCARScreenSpaceAimSample>& Targets,
		const FVector2D& AimViewport01,
		float MaxBoneDistanceNormalized,
		float BoundsPaddingNormalized,
		float HeadRegionScale,
		float TorsoRegionScale,
		float LegRegionScale,
		float MaxTargetAgeSeconds,
		double NowSeconds,
		int32& OutTargetIndex,
		bool& bOutIsHeadshot);

	bool ResolveHitViewportOnSample(
		const FSCARScreenSpaceAimSample& Sample,
		const FVector2D& AimViewport01,
		FVector2D& OutHitViewport01,
		ESCARVisionBodyJoint& OutHitJoint);

	bool ResolveHitImageUVOnSample(
		const FSCARScreenSpaceAimSample& Sample,
		const FVector2D& AimViewport01,
		FVector2D& OutHitImageUV,
		ESCARVisionBodyJoint& OutHitJoint);

	bool ResolveHitBoneAnchorOnSample(
		const FSCARScreenSpaceAimSample& Sample,
		const FVector2D& AimViewport01,
		FVector2D& OutHitImageUV,
		ESCARVisionBodyJoint& OutAnchorJointA,
		ESCARVisionBodyJoint& OutAnchorJointB,
		float& OutBoneT);

	bool TryGetTrackedHitViewport01FromVision(
		const TArray<FSCARScreenSpaceBodyTarget>& VisionTargets,
		int32 TargetId,
		ESCARVisionBodyJoint AnchorJointA,
		ESCARVisionBodyJoint AnchorJointB,
		float BoneT,
		FVector2D& OutViewport01);

	bool Viewport01ToWorldAtDistance(
		APlayerController* PlayerController,
		const FVector2D& Viewport01,
		float DistanceCentimeters,
		FVector& OutWorldLocation);

	float ComputeHitRegionScreenDiameter(
		const FSCARScreenSpaceAimSample& Sample,
		ESCARBodyHitRegion HitRegion,
		APlayerController* PlayerController,
		float MinScreenPixels = 18.f,
		float MaxScreenFraction = 0.2f);

	bool TryGetTrackedJointViewport01(
		const TArray<FSCARScreenSpaceAimSample>& Samples,
		int32 TargetId,
		ESCARVisionBodyJoint Joint,
		const FVector2D& ImageOffset,
		FVector2D& OutViewport01);
}
