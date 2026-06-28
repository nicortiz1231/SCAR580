#include "SCARScreenSpaceBodyTargeting.h"

#include "ARTypes.h"
#include "GameFramework/PlayerController.h"
#include "SCARBodyScreenMapping.h"
#include "SCARBodyPose2DMapping.h"
#include "SCARVisionBodyPoseProvider.h"

namespace SCARScreenSpaceBodyTargeting
{
	static bool AccumulateRegionBounds(
		const FSCARScreenSpaceAimSample& Sample,
		const TArray<int32>& JointIndices,
		FVector2D& OutMin,
		FVector2D& OutMax)
	{
		bool bFoundAny = false;
		for (const int32 Index : JointIndices)
		{
			if (!Sample.JointValid.IsValidIndex(Index) || !Sample.JointValid[Index])
			{
				continue;
			}

			const FVector2D& Point = Sample.JointViewport01[Index];
			if (!bFoundAny)
			{
				OutMin = Point;
				OutMax = Point;
				bFoundAny = true;
				continue;
			}

			OutMin.X = FMath::Min(OutMin.X, Point.X);
			OutMin.Y = FMath::Min(OutMin.Y, Point.Y);
			OutMax.X = FMath::Max(OutMax.X, Point.X);
			OutMax.Y = FMath::Max(OutMax.Y, Point.Y);
		}

		return bFoundAny;
	}

	namespace
	{
		constexpr int32 VisionJointCount = static_cast<int32>(ESCARVisionBodyJoint::Count);

		const int32 ParentIndices[VisionJointCount] =
		{
			static_cast<int32>(ESCARVisionBodyJoint::Neck),
			static_cast<int32>(ESCARVisionBodyJoint::Nose),
			static_cast<int32>(ESCARVisionBodyJoint::Nose),
			static_cast<int32>(ESCARVisionBodyJoint::LeftEye),
			static_cast<int32>(ESCARVisionBodyJoint::RightEye),
			static_cast<int32>(ESCARVisionBodyJoint::Neck),
			static_cast<int32>(ESCARVisionBodyJoint::Neck),
			static_cast<int32>(ESCARVisionBodyJoint::Root),
			static_cast<int32>(ESCARVisionBodyJoint::LeftShoulder),
			static_cast<int32>(ESCARVisionBodyJoint::RightShoulder),
			static_cast<int32>(ESCARVisionBodyJoint::LeftElbow),
			static_cast<int32>(ESCARVisionBodyJoint::RightElbow),
			static_cast<int32>(ESCARVisionBodyJoint::Root),
			static_cast<int32>(ESCARVisionBodyJoint::Root),
			INDEX_NONE,
			static_cast<int32>(ESCARVisionBodyJoint::LeftHip),
			static_cast<int32>(ESCARVisionBodyJoint::RightHip),
			static_cast<int32>(ESCARVisionBodyJoint::LeftKnee),
			static_cast<int32>(ESCARVisionBodyJoint::RightKnee),
		};

		float DistancePointToSegment(const FVector2D& Point, const FVector2D& A, const FVector2D& B)
		{
			const FVector2D AB = B - A;
			const float Denom = FMath::Max(AB.SizeSquared(), KINDA_SMALL_NUMBER);
			const float T = FMath::Clamp(FVector2D::DotProduct(Point - A, AB) / Denom, 0.f, 1.f);
			return FVector2D::Distance(Point, A + AB * T);
		}

		bool IsJointValid(const FSCARScreenSpaceAimSample& Sample, int32 Index)
		{
			return Sample.JointValid.IsValidIndex(Index) && Sample.JointValid[Index];
		}

		bool IsJointImageValid(const FSCARScreenSpaceAimSample& Sample, int32 Index)
		{
			return IsJointValid(Sample, Index)
				&& Sample.JointImageUV.IsValidIndex(Index)
				&& Sample.JointImageUV[Index].X >= 0.f
				&& Sample.JointImageUV[Index].Y >= 0.f;
		}

		bool MapVisionUVToViewport01(const FVector2D& VisionUV, FVector2D& OutViewport01)
		{
			OutViewport01 = USCARVisionBodyPoseProvider::NormalizedToViewport01(VisionUV);
			return true;
		}

		bool MapBoundsVisionToViewport01(const FVector4& BoundsVision, FVector4& OutBoundsViewport01)
		{
			const FVector2D CornerMin = USCARVisionBodyPoseProvider::NormalizedToViewport01(
				FVector2D(BoundsVision.X, BoundsVision.Y));
			const FVector2D CornerMax = USCARVisionBodyPoseProvider::NormalizedToViewport01(
				FVector2D(BoundsVision.Z, BoundsVision.W));
			OutBoundsViewport01 = FVector4(
				FMath::Min(CornerMin.X, CornerMax.X),
				FMath::Min(CornerMin.Y, CornerMax.Y),
				FMath::Max(CornerMin.X, CornerMax.X),
				FMath::Max(CornerMin.Y, CornerMax.Y));
			return true;
		}

		bool MapImageUVToViewport01(const FVector2D& ImageUV, FVector2D& OutViewport01)
		{
			if (SCARBodyScreenMapping::MapImageNormalizedToViewport01(ImageUV, OutViewport01))
			{
				return true;
			}

			OutViewport01 = USCARVisionBodyPoseProvider::NormalizedToViewport01(ImageUV);
			return false;
		}

		bool MapBoundsImageToViewport01(const FVector4& BoundsImage, FVector4& OutBoundsViewport01)
		{
			FVector2D CornerA;
			FVector2D CornerB;
			FVector2D CornerC;
			FVector2D CornerD;
			if (!MapImageUVToViewport01(FVector2D(BoundsImage.X, BoundsImage.Y), CornerA)
				|| !MapImageUVToViewport01(FVector2D(BoundsImage.Z, BoundsImage.Y), CornerB)
				|| !MapImageUVToViewport01(FVector2D(BoundsImage.X, BoundsImage.W), CornerC)
				|| !MapImageUVToViewport01(FVector2D(BoundsImage.Z, BoundsImage.W), CornerD))
			{
				return false;
			}

			OutBoundsViewport01.X = FMath::Min(FMath::Min(CornerA.X, CornerB.X), FMath::Min(CornerC.X, CornerD.X));
			OutBoundsViewport01.Y = FMath::Min(FMath::Min(CornerA.Y, CornerB.Y), FMath::Min(CornerC.Y, CornerD.Y));
			OutBoundsViewport01.Z = FMath::Max(FMath::Max(CornerA.X, CornerB.X), FMath::Max(CornerC.X, CornerD.X));
			OutBoundsViewport01.W = FMath::Max(FMath::Max(CornerA.Y, CornerB.Y), FMath::Max(CornerC.Y, CornerD.Y));
			return true;
		}

		float GetRegionScale(
			const FVector4& Bounds,
			const FVector2D& AimViewport01,
			float HeadRegionScale,
			float TorsoRegionScale,
			float LegRegionScale)
		{
			const float MinY = Bounds.Y;
			const float MaxY = Bounds.W;
			const float NormalizedBodyY = FMath::GetMappedRangeValueClamped(
				FVector2D(MinY, MaxY),
				FVector2D(0.f, 1.f),
				AimViewport01.Y);

			// UE viewport Y grows downward: 0 near the head, 1 near the feet.
			if (NormalizedBodyY <= 0.32f)
			{
				return FMath::Clamp(HeadRegionScale, 0.1f, 1.f);
			}

			if (NormalizedBodyY >= 0.74f)
			{
				return FMath::Clamp(LegRegionScale, 0.1f, 1.f);
			}

			return FMath::Clamp(TorsoRegionScale, 0.1f, 1.f);
		}

		float GetNormalizedBodyY(const FVector4& Bounds, const FVector2D& AimViewport01)
		{
			return FMath::GetMappedRangeValueClamped(
				FVector2D(Bounds.Y, Bounds.W),
				FVector2D(0.f, 1.f),
				AimViewport01.Y);
		}

		ESCARBodyHitRegion GetHitRegionFromNormalizedBodyY(const float NormalizedBodyY)
		{
			if (NormalizedBodyY <= 0.32f)
			{
				return ESCARBodyHitRegion::Head;
			}

			if (NormalizedBodyY >= 0.74f)
			{
				return ESCARBodyHitRegion::Legs;
			}

			return ESCARBodyHitRegion::Torso;
		}

		void GetRegionJointIndices(const ESCARBodyHitRegion HitRegion, TArray<int32>& OutJointIndices)
		{
			OutJointIndices.Reset();
			switch (HitRegion)
			{
			case ESCARBodyHitRegion::Head:
				OutJointIndices = {
					static_cast<int32>(ESCARVisionBodyJoint::Nose),
					static_cast<int32>(ESCARVisionBodyJoint::LeftEye),
					static_cast<int32>(ESCARVisionBodyJoint::RightEye),
					static_cast<int32>(ESCARVisionBodyJoint::LeftEar),
					static_cast<int32>(ESCARVisionBodyJoint::RightEar),
					static_cast<int32>(ESCARVisionBodyJoint::Neck),
				};
				break;
			case ESCARBodyHitRegion::Legs:
				OutJointIndices = {
					static_cast<int32>(ESCARVisionBodyJoint::LeftHip),
					static_cast<int32>(ESCARVisionBodyJoint::RightHip),
					static_cast<int32>(ESCARVisionBodyJoint::LeftKnee),
					static_cast<int32>(ESCARVisionBodyJoint::RightKnee),
					static_cast<int32>(ESCARVisionBodyJoint::LeftAnkle),
					static_cast<int32>(ESCARVisionBodyJoint::RightAnkle),
				};
				break;
			default:
				OutJointIndices = {
					static_cast<int32>(ESCARVisionBodyJoint::Neck),
					static_cast<int32>(ESCARVisionBodyJoint::LeftShoulder),
					static_cast<int32>(ESCARVisionBodyJoint::RightShoulder),
					static_cast<int32>(ESCARVisionBodyJoint::LeftElbow),
					static_cast<int32>(ESCARVisionBodyJoint::RightElbow),
					static_cast<int32>(ESCARVisionBodyJoint::Root),
					static_cast<int32>(ESCARVisionBodyJoint::LeftHip),
					static_cast<int32>(ESCARVisionBodyJoint::RightHip),
				};
				break;
			}
		}

		bool ComputeExpandedBodyHitBounds(
			const FVector4& BodyBounds,
			const float BoundsPadding,
			const float ExpandFraction,
			FVector4& OutHitBounds)
		{
			const float BodyWidth = FMath::Max(BodyBounds.Z - BodyBounds.X, KINDA_SMALL_NUMBER);
			const float BodyHeight = FMath::Max(BodyBounds.W - BodyBounds.Y, KINDA_SMALL_NUMBER);
			const float ExpandX = FMath::Max(BoundsPadding, BodyWidth * ExpandFraction);
			const float ExpandY = FMath::Max(BoundsPadding, BodyHeight * ExpandFraction);
			OutHitBounds = FVector4(
				BodyBounds.X - ExpandX,
				BodyBounds.Y - ExpandY,
				BodyBounds.Z + ExpandX,
				BodyBounds.W + ExpandY);
			return OutHitBounds.Z > OutHitBounds.X && OutHitBounds.W > OutHitBounds.Y;
		}

		bool IsAimInsideBodyHitBounds(
			const FSCARScreenSpaceAimSample& Sample,
			const FVector2D& AimViewport01,
			const float BoundsPadding,
			const float ExpandFraction)
		{
			FVector4 HitBounds;
			if (!ComputeExpandedBodyHitBounds(Sample.BoundsViewport01, BoundsPadding, ExpandFraction, HitBounds))
			{
				return false;
			}

			return AimViewport01.X >= HitBounds.X
				&& AimViewport01.X <= HitBounds.Z
				&& AimViewport01.Y >= HitBounds.Y
				&& AimViewport01.Y <= HitBounds.W;
		}

		bool IsHeadshotAim(const FSCARScreenSpaceAimSample& Sample, const FVector2D& AimViewport01, float Threshold)
		{
			for (int32 Index = 0; Index <= static_cast<int32>(ESCARVisionBodyJoint::RightEar); ++Index)
			{
				if (IsJointValid(Sample, Index)
					&& FVector2D::Distance(AimViewport01, Sample.JointViewport01[Index]) <= Threshold)
				{
					return true;
				}
			}

			if (!IsJointValid(Sample, static_cast<int32>(ESCARVisionBodyJoint::LeftShoulder))
				|| !IsJointValid(Sample, static_cast<int32>(ESCARVisionBodyJoint::RightShoulder)))
			{
				return false;
			}

			const float ShoulderY = FMath::Max(
				Sample.JointViewport01[static_cast<int32>(ESCARVisionBodyJoint::LeftShoulder)].Y,
				Sample.JointViewport01[static_cast<int32>(ESCARVisionBodyJoint::RightShoulder)].Y);
			return AimViewport01.Y <= ShoulderY - 0.02f;
		}

		bool ClassifyHeadshotOnSample(
			const FSCARScreenSpaceAimSample& Sample,
			const FVector2D& AimViewport01)
		{
			const float NormalizedBodyY = GetNormalizedBodyY(Sample.BoundsViewport01, AimViewport01);
			if (NormalizedBodyY <= 0.32f)
			{
				return true;
			}

			const float BodyWidth = FMath::Max(
				Sample.BoundsViewport01.Z - Sample.BoundsViewport01.X,
				KINDA_SMALL_NUMBER);
			return IsHeadshotAim(Sample, AimViewport01, FMath::Max(BodyWidth * 0.35f, 0.03f));
		}

		float ComputeAimDistanceToBodyCenter(
			const FSCARScreenSpaceAimSample& Sample,
			const FVector2D& AimViewport01)
		{
			const FVector4& Bounds = Sample.BoundsViewport01;
			const FVector2D Center((Bounds.X + Bounds.Z) * 0.5f, (Bounds.Y + Bounds.W) * 0.5f);
			return FVector2D::Distance(AimViewport01, Center);
		}

		bool TryGetAimDistanceOnSample(
			const FSCARScreenSpaceAimSample& Sample,
			const FVector2D& AimViewport01,
			const float BoundsPadding,
			const float ExpandFraction,
			float& OutBestDistance,
			bool& bOutIsHeadshot)
		{
			OutBestDistance = MAX_FLT;
			bOutIsHeadshot = false;

			if (!IsAimInsideBodyHitBounds(Sample, AimViewport01, BoundsPadding, ExpandFraction))
			{
				return false;
			}

			OutBestDistance = ComputeAimDistanceToBodyCenter(Sample, AimViewport01);
			bOutIsHeadshot = ClassifyHeadshotOnSample(Sample, AimViewport01);
			return true;
		}
	}

	bool BuildVisionAimSample(const FSCARScreenSpaceBodyTarget& Target, FSCARScreenSpaceAimSample& OutSample)
	{
		OutSample = FSCARScreenSpaceAimSample();
		OutSample.TargetId = Target.LocalId;
		OutSample.LastSeenTimeSeconds = Target.LastSeenTimeSeconds;
		OutSample.JointViewport01.SetNum(Target.Joints.Num());
		OutSample.JointValid.SetNum(Target.Joints.Num());
		OutSample.JointImageUV.SetNum(Target.Joints.Num());

		if (!MapBoundsVisionToViewport01(Target.Bounds, OutSample.BoundsViewport01))
		{
			const FVector2D BoundsMin = USCARVisionBodyPoseProvider::NormalizedToViewport01(
				FVector2D(Target.Bounds.X, Target.Bounds.Y));
			const FVector2D BoundsMax = USCARVisionBodyPoseProvider::NormalizedToViewport01(
				FVector2D(Target.Bounds.Z, Target.Bounds.W));
			OutSample.BoundsViewport01 = FVector4(
				FMath::Min(BoundsMin.X, BoundsMax.X),
				FMath::Min(BoundsMin.Y, BoundsMax.Y),
				FMath::Max(BoundsMin.X, BoundsMax.X),
				FMath::Max(BoundsMin.Y, BoundsMax.Y));
		}

		for (int32 Index = 0; Index < Target.Joints.Num(); ++Index)
		{
			const FSCARVisionBodyJoint& Joint = Target.Joints[Index];
			OutSample.JointValid[Index] = Joint.bIsValid;
			OutSample.JointImageUV[Index] = Joint.NormalizedPosition;
			if (!Joint.bIsValid)
			{
				continue;
			}

			MapVisionUVToViewport01(Joint.NormalizedPosition, OutSample.JointViewport01[Index]);
		}

		return Target.LocalId != INDEX_NONE;
	}

	bool BuildPose2DAimSample(
		const FARPose2D& Pose2D,
		APlayerController* PlayerController,
		const bool bFlipPose2DY,
		const bool bUseImageSpaceMapping,
		const int32 TargetId,
		FSCARScreenSpaceAimSample& OutSample)
	{
		OutSample = FSCARScreenSpaceAimSample();
		if (!PlayerController || Pose2D.JointLocations.Num() == 0)
		{
			return false;
		}

		int32 ScreenWidth = 0;
		int32 ScreenHeight = 0;
		PlayerController->GetViewportSize(ScreenWidth, ScreenHeight);
		if (ScreenWidth <= 0 || ScreenHeight <= 0)
		{
			return false;
		}

		OutSample.TargetId = TargetId;
		OutSample.LastSeenTimeSeconds = FPlatformTime::Seconds();
		OutSample.JointViewport01.SetNum(Pose2D.JointLocations.Num());
		OutSample.JointValid.SetNum(Pose2D.JointLocations.Num());
		OutSample.JointImageUV.SetNum(Pose2D.JointLocations.Num());

		const bool bNormalized = SCARBodyPose2DMapping::DetectPose2DNormalized(Pose2D);
		FVector2D ImageResolution(1920.f, 1440.f);
		SCARBodyScreenMapping::GetCameraImageResolution(ImageResolution);

		float MinX = 1.f;
		float MinY = 1.f;
		float MaxX = 0.f;
		float MaxY = 0.f;

		for (int32 Index = 0; Index < Pose2D.JointLocations.Num(); ++Index)
		{
			OutSample.JointValid[Index] = Pose2D.IsJointTracked.IsValidIndex(Index) && Pose2D.IsJointTracked[Index];
			OutSample.JointImageUV[Index] = FVector2D(-1.f, -1.f);
			if (!OutSample.JointValid[Index])
			{
				continue;
			}

			const FVector2D Raw = Pose2D.JointLocations[Index];
			FVector2D ImageUV = Raw;
			if (!bNormalized)
			{
				ImageUV = FVector2D(
					Raw.X / FMath::Max(ImageResolution.X, 1.f),
					Raw.Y / FMath::Max(ImageResolution.Y, 1.f));
			}

			OutSample.JointImageUV[Index] = ImageUV;

			FVector2D GuiPixels;
			if (!SCARBodyPose2DMapping::Pose2DJointToGuiPixels(
				Pose2D,
				Index,
				ScreenWidth,
				ScreenHeight,
				bFlipPose2DY,
				bUseImageSpaceMapping,
				GuiPixels))
			{
				OutSample.JointValid[Index] = false;
				continue;
			}

			const FVector2D Viewport01(GuiPixels.X / ScreenWidth, GuiPixels.Y / ScreenHeight);
			OutSample.JointViewport01[Index] = Viewport01;
			MinX = FMath::Min(MinX, Viewport01.X);
			MinY = FMath::Min(MinY, Viewport01.Y);
			MaxX = FMath::Max(MaxX, Viewport01.X);
			MaxY = FMath::Max(MaxY, Viewport01.Y);
		}

		OutSample.BoundsViewport01 = FVector4(MinX, MinY, MaxX, MaxY);
		return MaxX > MinX && MaxY > MinY;
	}

	bool TryGetBestTarget(
		const TArray<FSCARScreenSpaceAimSample>& Targets,
		const FVector2D& AimViewport01,
		const float BoundsPaddingNormalized,
		const float BodyHitBoundsExpandFraction,
		const float MaxTargetAgeSeconds,
		const double NowSeconds,
		int32& OutTargetIndex,
		bool& bOutIsHeadshot)
	{
		OutTargetIndex = INDEX_NONE;
		bOutIsHeadshot = false;

		float BestDistance = MAX_FLT;
		for (int32 TargetIndex = 0; TargetIndex < Targets.Num(); ++TargetIndex)
		{
			const FSCARScreenSpaceAimSample& Sample = Targets[TargetIndex];
			if (NowSeconds - Sample.LastSeenTimeSeconds > MaxTargetAgeSeconds)
			{
				continue;
			}

			float Distance = MAX_FLT;
			bool bHeadshot = false;
			if (!TryGetAimDistanceOnSample(
				Sample,
				AimViewport01,
				BoundsPaddingNormalized,
				BodyHitBoundsExpandFraction,
				Distance,
				bHeadshot))
			{
				continue;
			}

			if (Distance < BestDistance)
			{
				BestDistance = Distance;
				OutTargetIndex = TargetIndex;
				bOutIsHeadshot = bHeadshot;
			}
		}

		return Targets.IsValidIndex(OutTargetIndex);
	}

	bool ResolveHitViewportOnSample(
		const FSCARScreenSpaceAimSample& Sample,
		const FVector2D& AimViewport01,
		FVector2D& OutHitViewport01,
		ESCARVisionBodyJoint& OutHitJoint)
	{
		float BestDistance = MAX_FLT;
		OutHitViewport01 = AimViewport01;
		OutHitJoint = ESCARVisionBodyJoint::Root;

		for (int32 Index = 0; Index < Sample.JointViewport01.Num(); ++Index)
		{
			if (!IsJointValid(Sample, Index))
			{
				continue;
			}

			const float Distance = FVector2D::Distance(AimViewport01, Sample.JointViewport01[Index]);
			if (Distance < BestDistance)
			{
				BestDistance = Distance;
				OutHitViewport01 = Sample.JointViewport01[Index];
				OutHitJoint = static_cast<ESCARVisionBodyJoint>(Index);
			}
		}

		for (int32 Index = 0; Index < VisionJointCount; ++Index)
		{
			const int32 ParentIndex = ParentIndices[Index];
			if (ParentIndex < 0 || !IsJointValid(Sample, Index) || !IsJointValid(Sample, ParentIndex))
			{
				continue;
			}

			const FVector2D& A = Sample.JointViewport01[Index];
			const FVector2D& B = Sample.JointViewport01[ParentIndex];
			const FVector2D AB = B - A;
			const float Denom = FMath::Max(AB.SizeSquared(), KINDA_SMALL_NUMBER);
			const float T = FMath::Clamp(FVector2D::DotProduct(AimViewport01 - A, AB) / Denom, 0.f, 1.f);
			const FVector2D Closest = A + AB * T;
			const float Distance = FVector2D::Distance(AimViewport01, Closest);
			if (Distance < BestDistance)
			{
				BestDistance = Distance;
				OutHitViewport01 = Closest;
				OutHitJoint = static_cast<ESCARVisionBodyJoint>(Index);
			}
		}

		return BestDistance < MAX_FLT;
	}

	bool ResolveHitBoneAnchorOnSample(
		const FSCARScreenSpaceAimSample& Sample,
		const FVector2D& AimViewport01,
		FVector2D& OutHitImageUV,
		ESCARVisionBodyJoint& OutAnchorJointA,
		ESCARVisionBodyJoint& OutAnchorJointB,
		float& OutBoneT)
	{
		float BestDistance = MAX_FLT;
		OutHitImageUV = FVector2D::ZeroVector;
		OutAnchorJointA = ESCARVisionBodyJoint::Root;
		OutAnchorJointB = ESCARVisionBodyJoint::Root;
		OutBoneT = 0.f;
		bool bUsedSegment = false;

		for (int32 Index = 0; Index < Sample.JointViewport01.Num(); ++Index)
		{
			if (!IsJointImageValid(Sample, Index))
			{
				continue;
			}

			const float Distance = FVector2D::Distance(AimViewport01, Sample.JointViewport01[Index]);
			if (Distance < BestDistance)
			{
				BestDistance = Distance;
				OutHitImageUV = Sample.JointImageUV[Index];
				OutAnchorJointA = static_cast<ESCARVisionBodyJoint>(Index);
				OutAnchorJointB = OutAnchorJointA;
				OutBoneT = 0.f;
				bUsedSegment = false;
			}
		}

		for (int32 Index = 0; Index < VisionJointCount; ++Index)
		{
			const int32 ParentIndex = ParentIndices[Index];
			if (ParentIndex < 0
				|| !IsJointImageValid(Sample, Index)
				|| !IsJointImageValid(Sample, ParentIndex))
			{
				continue;
			}

			const FVector2D& ViewportA = Sample.JointViewport01[Index];
			const FVector2D& ViewportB = Sample.JointViewport01[ParentIndex];
			const FVector2D ViewportAB = ViewportB - ViewportA;
			const float Denom = FMath::Max(ViewportAB.SizeSquared(), KINDA_SMALL_NUMBER);
			const float T = FMath::Clamp(FVector2D::DotProduct(AimViewport01 - ViewportA, ViewportAB) / Denom, 0.f, 1.f);
			const FVector2D ClosestViewport = ViewportA + ViewportAB * T;
			const float Distance = FVector2D::Distance(AimViewport01, ClosestViewport);
			if (Distance < BestDistance)
			{
				const FVector2D& ImageA = Sample.JointImageUV[Index];
				const FVector2D& ImageB = Sample.JointImageUV[ParentIndex];
				const FVector2D ImageAB = ImageB - ImageA;
				BestDistance = Distance;
				OutHitImageUV = ImageA + ImageAB * T;
				OutAnchorJointA = static_cast<ESCARVisionBodyJoint>(Index);
				OutAnchorJointB = static_cast<ESCARVisionBodyJoint>(ParentIndex);
				const float ImageDenom = FMath::Max(ImageAB.SizeSquared(), KINDA_SMALL_NUMBER);
				OutBoneT = FMath::Clamp(FVector2D::DotProduct(OutHitImageUV - ImageA, ImageAB) / ImageDenom, 0.f, 1.f);
				bUsedSegment = true;
			}
		}

		(void)bUsedSegment;
		return BestDistance < MAX_FLT;
	}

	bool ResolveHitImageUVOnSample(
		const FSCARScreenSpaceAimSample& Sample,
		const FVector2D& AimViewport01,
		FVector2D& OutHitImageUV,
		ESCARVisionBodyJoint& OutHitJoint)
	{
		ESCARVisionBodyJoint AnchorJointB = ESCARVisionBodyJoint::Root;
		float BoneT = 0.f;
		if (!ResolveHitBoneAnchorOnSample(
			Sample,
			AimViewport01,
			OutHitImageUV,
			OutHitJoint,
			AnchorJointB,
			BoneT))
		{
			return false;
		}

		return true;
	}

	const FSCARScreenSpaceBodyTarget* FindVisionTargetById(
		const TArray<FSCARScreenSpaceBodyTarget>& VisionTargets,
		const int32 TargetId)
	{
		for (const FSCARScreenSpaceBodyTarget& Target : VisionTargets)
		{
			if (Target.LocalId == TargetId)
			{
				return &Target;
			}
		}

		if (VisionTargets.Num() == 1)
		{
			return &VisionTargets[0];
		}

		return nullptr;
	}

	bool TryGetVisionJointImageUV(
		const FSCARScreenSpaceBodyTarget& Target,
		const int32 JointIndex,
		FVector2D& OutImageUV)
	{
		if (!Target.Joints.IsValidIndex(JointIndex) || !Target.Joints[JointIndex].bIsValid)
		{
			return false;
		}

		OutImageUV = Target.Joints[JointIndex].NormalizedPosition;
		return OutImageUV.X >= 0.f && OutImageUV.Y >= 0.f;
	}

	bool TryGetTrackedHitViewport01FromVision(
		const TArray<FSCARScreenSpaceBodyTarget>& VisionTargets,
		const int32 TargetId,
		const ESCARVisionBodyJoint AnchorJointA,
		const ESCARVisionBodyJoint AnchorJointB,
		const float BoneT,
		FVector2D& OutViewport01)
	{
		const FSCARScreenSpaceBodyTarget* Target = FindVisionTargetById(VisionTargets, TargetId);
		if (!Target)
		{
			return false;
		}

		const int32 IndexA = static_cast<int32>(AnchorJointA);
		const int32 IndexB = static_cast<int32>(AnchorJointB);
		FVector2D ImageA;
		FVector2D ImageB;
		if (!TryGetVisionJointImageUV(*Target, IndexA, ImageA) || !TryGetVisionJointImageUV(*Target, IndexB, ImageB))
		{
			return false;
		}

		const FVector2D HitImageUV = FMath::Lerp(ImageA, ImageB, FMath::Clamp(BoneT, 0.f, 1.f));
		return MapVisionUVToViewport01(HitImageUV, OutViewport01);
	}

	bool Viewport01ToWorldAtDistance(
		APlayerController* PlayerController,
		const FVector2D& Viewport01,
		const float DistanceCentimeters,
		FVector& OutWorldLocation)
	{
		if (!PlayerController)
		{
			return false;
		}

		int32 SizeX = 0;
		int32 SizeY = 0;
		PlayerController->GetViewportSize(SizeX, SizeY);
		if (SizeX <= 0 || SizeY <= 0)
		{
			return false;
		}

		FVector WorldLocation;
		FVector WorldDirection;
		if (!PlayerController->DeprojectScreenPositionToWorld(
			Viewport01.X * SizeX,
			Viewport01.Y * SizeY,
			WorldLocation,
			WorldDirection))
		{
			return false;
		}

		OutWorldLocation = WorldLocation + WorldDirection * DistanceCentimeters;
		return true;
	}

	float ComputeRegionViewportDiameter(
		const FSCARScreenSpaceAimSample& Sample,
		const ESCARBodyHitRegion HitRegion)
	{
		TArray<int32> JointIndices;
		switch (HitRegion)
		{
		case ESCARBodyHitRegion::Head:
			JointIndices = {
				static_cast<int32>(ESCARVisionBodyJoint::Nose),
				static_cast<int32>(ESCARVisionBodyJoint::LeftEye),
				static_cast<int32>(ESCARVisionBodyJoint::RightEye),
				static_cast<int32>(ESCARVisionBodyJoint::LeftEar),
				static_cast<int32>(ESCARVisionBodyJoint::RightEar),
				static_cast<int32>(ESCARVisionBodyJoint::Neck),
			};
			break;
		case ESCARBodyHitRegion::Legs:
			JointIndices = {
				static_cast<int32>(ESCARVisionBodyJoint::LeftHip),
				static_cast<int32>(ESCARVisionBodyJoint::RightHip),
				static_cast<int32>(ESCARVisionBodyJoint::LeftKnee),
				static_cast<int32>(ESCARVisionBodyJoint::RightKnee),
				static_cast<int32>(ESCARVisionBodyJoint::LeftAnkle),
				static_cast<int32>(ESCARVisionBodyJoint::RightAnkle),
			};
			break;
		case ESCARBodyHitRegion::Torso:
		default:
			JointIndices = {
				static_cast<int32>(ESCARVisionBodyJoint::Neck),
				static_cast<int32>(ESCARVisionBodyJoint::LeftShoulder),
				static_cast<int32>(ESCARVisionBodyJoint::RightShoulder),
				static_cast<int32>(ESCARVisionBodyJoint::LeftElbow),
				static_cast<int32>(ESCARVisionBodyJoint::RightElbow),
				static_cast<int32>(ESCARVisionBodyJoint::Root),
				static_cast<int32>(ESCARVisionBodyJoint::LeftHip),
				static_cast<int32>(ESCARVisionBodyJoint::RightHip),
			};
			break;
		}

		FVector2D RegionMin;
		FVector2D RegionMax;
		if (AccumulateRegionBounds(Sample, JointIndices, RegionMin, RegionMax))
		{
			return FMath::Max(RegionMax.X - RegionMin.X, RegionMax.Y - RegionMin.Y);
		}

		const FVector4& Bounds = Sample.BoundsViewport01;
		const float BodyWidth = FMath::Max(0.f, Bounds.Z - Bounds.X);
		const float BodyHeight = FMath::Max(0.f, Bounds.W - Bounds.Y);
		switch (HitRegion)
		{
		case ESCARBodyHitRegion::Head:
			return FMath::Max(BodyWidth * 0.28f, BodyHeight * 0.14f);
		case ESCARBodyHitRegion::Legs:
			return FMath::Max(BodyWidth * 0.34f, BodyHeight * 0.28f);
		default:
			return FMath::Max(BodyWidth * 0.42f, BodyHeight * 0.24f);
		}
	}

	float ComputeHitRegionScreenDiameter(
		const FSCARScreenSpaceAimSample& Sample,
		const ESCARBodyHitRegion HitRegion,
		APlayerController* PlayerController,
		const float MinScreenPixels,
		const float MaxScreenFraction)
	{
		if (!PlayerController)
		{
			return MinScreenPixels;
		}

		int32 SizeX = 0;
		int32 SizeY = 0;
		PlayerController->GetViewportSize(SizeX, SizeY);
		if (SizeX <= 0 || SizeY <= 0)
		{
			return MinScreenPixels;
		}

		const float ReferencePixels = static_cast<float>(FMath::Min(SizeX, SizeY));
		const float Diameter01 = ComputeRegionViewportDiameter(Sample, HitRegion);
		float ScreenDiameter = Diameter01 * ReferencePixels;

		switch (HitRegion)
		{
		case ESCARBodyHitRegion::Head:
			ScreenDiameter *= 0.95f;
			break;
		case ESCARBodyHitRegion::Legs:
			ScreenDiameter *= 0.55f;
			break;
		default:
			ScreenDiameter *= 0.45f;
			break;
		}

		return FMath::Clamp(ScreenDiameter, MinScreenPixels, ReferencePixels * MaxScreenFraction);
	}

	bool TryGetTrackedJointViewport01(
		const TArray<FSCARScreenSpaceAimSample>& Samples,
		const int32 TargetId,
		const ESCARVisionBodyJoint Joint,
		const FVector2D& ImageOffset,
		FVector2D& OutViewport01)
	{
		const int32 JointIndex = static_cast<int32>(Joint);
		for (const FSCARScreenSpaceAimSample& Sample : Samples)
		{
			if (Sample.TargetId != TargetId)
			{
				continue;
			}

			if (!IsJointImageValid(Sample, JointIndex))
			{
				continue;
			}

			const FVector2D HitImageUV = Sample.JointImageUV[JointIndex] + ImageOffset;
			if (MapImageUVToViewport01(HitImageUV, OutViewport01))
			{
				return true;
			}
		}

		if (Samples.Num() == 1 && IsJointImageValid(Samples[0], JointIndex))
		{
			const FVector2D HitImageUV = Samples[0].JointImageUV[JointIndex] + ImageOffset;
			return MapImageUVToViewport01(HitImageUV, OutViewport01);
		}

		for (const FSCARScreenSpaceAimSample& Sample : Samples)
		{
			if (Sample.TargetId != TargetId || !IsJointValid(Sample, JointIndex))
			{
				continue;
			}

			OutViewport01 = Sample.JointViewport01[JointIndex] + ImageOffset;
			return true;
		}

		if (Samples.Num() == 1 && IsJointValid(Samples[0], JointIndex))
		{
			OutViewport01 = Samples[0].JointViewport01[JointIndex] + ImageOffset;
			return true;
		}

		return false;
	}
}
