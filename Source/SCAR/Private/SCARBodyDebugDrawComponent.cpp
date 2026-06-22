#include "SCARBodyDebugDrawComponent.h"

#include "ARTrackable.h"
#include "Debug/DebugDrawService.h"
#include "DrawDebugHelpers.h"
#include "Engine/Canvas.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "SCARBodyDetectionSubsystem.h"
#include "SCARBodyDetectionTypes.h"
#include "SCARBodyPose2DMapping.h"
#include "SCARBodyScreenMapping.h"

USCARBodyDebugDrawComponent::USCARBodyDebugDrawComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.TickGroup = TG_PostUpdateWork;
}

void USCARBodyDebugDrawComponent::BeginPlay()
{
	Super::BeginPlay();

	if (!DebugDrawDelegateHandle.IsValid())
	{
		FDebugDrawDelegate DebugDrawDelegate;
		DebugDrawDelegate.BindUObject(this, &USCARBodyDebugDrawComponent::OnDebugDraw);
		DebugDrawDelegateHandle = UDebugDrawService::Register(TEXT("Game"), DebugDrawDelegate);
	}
}

void USCARBodyDebugDrawComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (DebugDrawDelegateHandle.IsValid())
	{
		UDebugDrawService::Unregister(DebugDrawDelegateHandle);
		DebugDrawDelegateHandle.Reset();
	}

	Super::EndPlay(EndPlayReason);
}

void USCARBodyDebugDrawComponent::TickComponent(
	const float DeltaTime,
	const ELevelTick TickType,
	FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	UWorld* World = GetWorld();
	if (!World)
	{
		bHasScreenOverlay = false;
		return;
	}

	const USCARBodyDetectionSubsystem* Subsystem = World->GetSubsystem<USCARBodyDetectionSubsystem>();
	if (!Subsystem || !Subsystem->IsPersonInCameraPreview())
	{
		bHasScreenOverlay = false;
		return;
	}

	const bool bCanDraw3D = bDraw3DSkeleton && Subsystem->Has3DBody();
	const bool bCanDrawPose2D = bDrawPose2D && Subsystem->HasPose2D();
	const bool bCanDrawVision = bDrawVisionSkeleton && Subsystem->HasVisionTarget();

	if (SourceMode == ESCARBodyDebugSourceMode::ARKit3D)
	{
		bHasScreenOverlay = false;
		if (bCanDraw3D)
		{
			DrawPose3D(Subsystem);
		}
		return;
	}

	if (SourceMode == ESCARBodyDebugSourceMode::All)
	{
		if (bCanDraw3D)
		{
			DrawPose3D(Subsystem);
		}
		UpdateScreenOverlayCache(Subsystem);
		return;
	}

	if (SourceMode == ESCARBodyDebugSourceMode::Pose2D || SourceMode == ESCARBodyDebugSourceMode::Auto)
	{
		if (SourceMode == ESCARBodyDebugSourceMode::Auto && !bCanDrawPose2D && bCanDraw3D)
		{
			CachePose3DProjectedScreenOverlay(Subsystem);
			return;
		}

		if (SourceMode == ESCARBodyDebugSourceMode::Auto && !bCanDrawPose2D && !bCanDraw3D && bCanDrawVision)
		{
			CacheVisionScreenOverlay(Subsystem);
			return;
		}

		if (bCanDrawPose2D)
		{
			CachePose2DScreenOverlay(Subsystem);
			return;
		}
	}

	if (SourceMode == ESCARBodyDebugSourceMode::Vision)
	{
		if (bCanDrawVision)
		{
			CacheVisionScreenOverlay(Subsystem);
			return;
		}
	}

	bHasScreenOverlay = false;
}

void USCARBodyDebugDrawComponent::OnDebugDraw(UCanvas* Canvas, APlayerController* PlayerController)
{
	if (!Canvas || !bHasScreenOverlay)
	{
		return;
	}

	(void)PlayerController;
	DrawScreenOverlay(Canvas);
}

void USCARBodyDebugDrawComponent::UpdateScreenOverlayCache(const USCARBodyDetectionSubsystem* Subsystem)
{
	if (bDrawPose2D && Subsystem->HasPose2D())
	{
		CachePose2DScreenOverlay(Subsystem);
		return;
	}

	if (bDrawVisionSkeleton && Subsystem->HasVisionTarget())
	{
		CacheVisionScreenOverlay(Subsystem);
	}
	else
	{
		bHasScreenOverlay = false;
	}
}

void USCARBodyDebugDrawComponent::CachePose2DScreenOverlay(const USCARBodyDetectionSubsystem* Subsystem)
{
	APlayerController* PlayerController = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
	if (!PlayerController || !Subsystem->HasPose2D())
	{
		bHasScreenOverlay = false;
		return;
	}

	int32 ScreenWidth = 0;
	int32 ScreenHeight = 0;
	PlayerController->GetViewportSize(ScreenWidth, ScreenHeight);
	if (ScreenWidth <= 0 || ScreenHeight <= 0)
	{
		bHasScreenOverlay = false;
		return;
	}

	const TArray<FARPose2D>& Poses2D = Subsystem->GetSnapshot().TrackedPoses2D;
	int32 BestPoseIndex = INDEX_NONE;
	int32 MostTrackedJoints = -1;
	for (int32 PoseIndex = 0; PoseIndex < Poses2D.Num(); ++PoseIndex)
	{
		int32 TrackedJointCount = 0;
		for (const bool bTracked : Poses2D[PoseIndex].IsJointTracked)
		{
			TrackedJointCount += bTracked ? 1 : 0;
		}
		if (TrackedJointCount > MostTrackedJoints)
		{
			MostTrackedJoints = TrackedJointCount;
			BestPoseIndex = PoseIndex;
		}
	}

	if (!Poses2D.IsValidIndex(BestPoseIndex))
	{
		bHasScreenOverlay = false;
		return;
	}

	const FARPose2D& Pose2D = Poses2D[BestPoseIndex];
	CachedScreenJoints.SetNum(Pose2D.JointLocations.Num());
	CachedBonePairs.Reset();

	for (int32 JointIndex = 0; JointIndex < Pose2D.JointLocations.Num(); ++JointIndex)
	{
		FSCARBodyDebugScreenJoint& Joint = CachedScreenJoints[JointIndex];
		Joint.bIsValid = false;

		if (!Pose2D.IsJointTracked.IsValidIndex(JointIndex) || !Pose2D.IsJointTracked[JointIndex])
		{
			continue;
		}

		FVector2D GuiPixels;
		if (!SCARBodyPose2DMapping::Pose2DJointToGuiPixels(
			Pose2D,
			JointIndex,
			ScreenWidth,
			ScreenHeight,
			bFlipPose2DY,
			bUseImageSpacePose2DMapping,
			GuiPixels))
		{
			continue;
		}

		Joint.GuiPosition = GuiPixels;
		Joint.bIsValid = true;
	}

	for (int32 JointIndex = 0; JointIndex < Pose2D.JointLocations.Num(); ++JointIndex)
	{
		const int32 ParentIndex = Pose2D.SkeletonDefinition.ParentIndices.IsValidIndex(JointIndex)
			? Pose2D.SkeletonDefinition.ParentIndices[JointIndex]
			: INDEX_NONE;
		if (ParentIndex < 0
			|| !CachedScreenJoints.IsValidIndex(JointIndex)
			|| !CachedScreenJoints.IsValidIndex(ParentIndex)
			|| !CachedScreenJoints[JointIndex].bIsValid
			|| !CachedScreenJoints[ParentIndex].bIsValid)
		{
			continue;
		}

		CachedBonePairs.Add(FIntPoint(JointIndex, ParentIndex));
	}

	CachedBoneColor = SkeletonColorPose2D;
	CachedJointColor = JointMarkerColor;
	bHasScreenOverlay = CachedBonePairs.Num() > 0 || CachedScreenJoints.ContainsByPredicate([](const FSCARBodyDebugScreenJoint& Joint)
	{
		return Joint.bIsValid;
	});
}

void USCARBodyDebugDrawComponent::CacheVisionScreenOverlay(const USCARBodyDetectionSubsystem* Subsystem)
{
	APlayerController* PlayerController = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
	if (!PlayerController || !Subsystem->HasVisionTarget())
	{
		bHasScreenOverlay = false;
		return;
	}

	int32 ScreenWidth = 0;
	int32 ScreenHeight = 0;
	PlayerController->GetViewportSize(ScreenWidth, ScreenHeight);
	if (ScreenWidth <= 0 || ScreenHeight <= 0)
	{
		bHasScreenOverlay = false;
		return;
	}

	static const TArray<TPair<int32, int32>> VisionBonePairs = {
		{static_cast<int32>(ESCARVisionBodyJoint::Neck), static_cast<int32>(ESCARVisionBodyJoint::Nose)},
		{static_cast<int32>(ESCARVisionBodyJoint::LeftShoulder), static_cast<int32>(ESCARVisionBodyJoint::Neck)},
		{static_cast<int32>(ESCARVisionBodyJoint::RightShoulder), static_cast<int32>(ESCARVisionBodyJoint::Neck)},
		{static_cast<int32>(ESCARVisionBodyJoint::LeftElbow), static_cast<int32>(ESCARVisionBodyJoint::LeftShoulder)},
		{static_cast<int32>(ESCARVisionBodyJoint::RightElbow), static_cast<int32>(ESCARVisionBodyJoint::RightShoulder)},
		{static_cast<int32>(ESCARVisionBodyJoint::LeftWrist), static_cast<int32>(ESCARVisionBodyJoint::LeftElbow)},
		{static_cast<int32>(ESCARVisionBodyJoint::RightWrist), static_cast<int32>(ESCARVisionBodyJoint::RightElbow)},
		{static_cast<int32>(ESCARVisionBodyJoint::Root), static_cast<int32>(ESCARVisionBodyJoint::Neck)},
		{static_cast<int32>(ESCARVisionBodyJoint::LeftHip), static_cast<int32>(ESCARVisionBodyJoint::Root)},
		{static_cast<int32>(ESCARVisionBodyJoint::RightHip), static_cast<int32>(ESCARVisionBodyJoint::Root)},
		{static_cast<int32>(ESCARVisionBodyJoint::LeftKnee), static_cast<int32>(ESCARVisionBodyJoint::LeftHip)},
		{static_cast<int32>(ESCARVisionBodyJoint::RightKnee), static_cast<int32>(ESCARVisionBodyJoint::RightHip)},
		{static_cast<int32>(ESCARVisionBodyJoint::LeftAnkle), static_cast<int32>(ESCARVisionBodyJoint::LeftKnee)},
		{static_cast<int32>(ESCARVisionBodyJoint::RightAnkle), static_cast<int32>(ESCARVisionBodyJoint::RightKnee)},
	};

	const TArray<FSCARScreenSpaceBodyTarget>& VisionTargets = Subsystem->GetSnapshot().VisionTargets;
	const int32 PrimaryTargetIndex = FindPrimaryVisionTargetIndex(VisionTargets);
	if (!VisionTargets.IsValidIndex(PrimaryTargetIndex))
	{
		bHasScreenOverlay = false;
		return;
	}

	const FSCARScreenSpaceBodyTarget& Target = VisionTargets[PrimaryTargetIndex];
	CachedScreenJoints.SetNum(FSCARScreenSpaceBodyTarget::JointCount);
	CachedBonePairs.Reset();

	for (int32 JointIndex = 0; JointIndex < Target.Joints.Num(); ++JointIndex)
	{
		FSCARBodyDebugScreenJoint& Joint = CachedScreenJoints[JointIndex];
		Joint.bIsValid = false;

		FVector2D GuiPixels;
		if (!VisionJointToGuiPixels(Target.Joints[JointIndex], ScreenWidth, ScreenHeight, GuiPixels))
		{
			continue;
		}

		Joint.GuiPosition = GuiPixels;
		Joint.bIsValid = true;
	}

	for (const TPair<int32, int32>& BonePair : VisionBonePairs)
	{
		if (!CachedScreenJoints.IsValidIndex(BonePair.Key)
			|| !CachedScreenJoints.IsValidIndex(BonePair.Value)
			|| !CachedScreenJoints[BonePair.Key].bIsValid
			|| !CachedScreenJoints[BonePair.Value].bIsValid)
		{
			continue;
		}

		CachedBonePairs.Add(FIntPoint(BonePair.Key, BonePair.Value));
	}

	CachedBoneColor = SkeletonColorVision;
	CachedJointColor = JointMarkerColor;
	bHasScreenOverlay = CachedBonePairs.Num() > 0;
}

void USCARBodyDebugDrawComponent::CachePose3DProjectedScreenOverlay(const USCARBodyDetectionSubsystem* Subsystem)
{
	APlayerController* PlayerController = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
	if (!PlayerController || !Subsystem->Has3DBody())
	{
		bHasScreenOverlay = false;
		return;
	}

	int32 ScreenWidth = 0;
	int32 ScreenHeight = 0;
	PlayerController->GetViewportSize(ScreenWidth, ScreenHeight);
	if (ScreenWidth <= 0 || ScreenHeight <= 0)
	{
		bHasScreenOverlay = false;
		return;
	}

	const FSCARBodyDetectionSnapshot& Snapshot = Subsystem->GetSnapshot();
	const FARPose3D& Pose = Snapshot.TrackedPose3D;
	const FTransform RootTransform = Snapshot.TrackedPose3DWorldTransform;

	CachedScreenJoints.SetNum(Pose.JointTransforms.Num());
	CachedBonePairs.Reset();

	for (int32 JointIndex = 0; JointIndex < Pose.JointTransforms.Num(); ++JointIndex)
	{
		FSCARBodyDebugScreenJoint& Joint = CachedScreenJoints[JointIndex];
		Joint.bIsValid = false;

		if (!Pose.IsJointTracked.IsValidIndex(JointIndex) || !Pose.IsJointTracked[JointIndex])
		{
			continue;
		}

		const FVector JointWorld = RootTransform.TransformPosition(Pose.JointTransforms[JointIndex].GetLocation());
		FVector2D ScreenPosition;
		if (!PlayerController->ProjectWorldLocationToScreen(JointWorld, ScreenPosition, true))
		{
			continue;
		}

		Joint.GuiPosition = ScreenPosition;
		Joint.bIsValid = true;
	}

	for (int32 JointIndex = 0; JointIndex < Pose.JointTransforms.Num(); ++JointIndex)
	{
		const int32 ParentIndex = Pose.SkeletonDefinition.ParentIndices.IsValidIndex(JointIndex)
			? Pose.SkeletonDefinition.ParentIndices[JointIndex]
			: INDEX_NONE;
		if (ParentIndex < 0
			|| !CachedScreenJoints.IsValidIndex(JointIndex)
			|| !CachedScreenJoints.IsValidIndex(ParentIndex)
			|| !CachedScreenJoints[JointIndex].bIsValid
			|| !CachedScreenJoints[ParentIndex].bIsValid)
		{
			continue;
		}

		CachedBonePairs.Add(FIntPoint(JointIndex, ParentIndex));
	}

	CachedBoneColor = SkeletonColor3D;
	CachedJointColor = JointMarkerColor;
	bHasScreenOverlay = CachedBonePairs.Num() > 0;
}

void USCARBodyDebugDrawComponent::DrawScreenOverlay(UCanvas* Canvas) const
{
	for (const FIntPoint& BonePair : CachedBonePairs)
	{
		if (!CachedScreenJoints.IsValidIndex(BonePair.X) || !CachedScreenJoints.IsValidIndex(BonePair.Y))
		{
			continue;
		}

		const FSCARBodyDebugScreenJoint& StartJoint = CachedScreenJoints[BonePair.X];
		const FSCARBodyDebugScreenJoint& EndJoint = CachedScreenJoints[BonePair.Y];
		if (!StartJoint.bIsValid || !EndJoint.bIsValid)
		{
			continue;
		}

		DrawGuiLine(Canvas, StartJoint.GuiPosition, EndJoint.GuiPosition, LineThickness, CachedBoneColor);
	}

	if (!bDrawJointMarkers)
	{
		return;
	}

	for (const FSCARBodyDebugScreenJoint& Joint : CachedScreenJoints)
	{
		if (!Joint.bIsValid)
		{
			continue;
		}

		DrawGuiJoint(Canvas, Joint.GuiPosition, ScreenJointPixelSize, CachedJointColor);
	}
}

void USCARBodyDebugDrawComponent::DrawGuiLine(
	UCanvas* Canvas,
	const FVector2D& Start,
	const FVector2D& End,
	const float Thickness,
	const FLinearColor& Color) const
{
	DrawDebugCanvas2DLine(Canvas, Start, End, Color, Thickness);
}

void USCARBodyDebugDrawComponent::DrawGuiJoint(
	UCanvas* Canvas,
	const FVector2D& Center,
	const float Size,
	const FLinearColor& Color) const
{
	const float HalfSize = Size * 0.5f;
	const FVector2D TopLeft(Center.X - HalfSize, Center.Y - HalfSize);
	const FVector2D BottomRight(Center.X + HalfSize, Center.Y + HalfSize);
	DrawDebugCanvas2DBox(Canvas, FBox2D(TopLeft, BottomRight), Color, 1.f);
}

void USCARBodyDebugDrawComponent::DrawPose3D(const USCARBodyDetectionSubsystem* Subsystem) const
{
	UWorld* World = GetWorld();
	if (!World || !Subsystem->Has3DBody())
	{
		return;
	}

	const FSCARBodyDetectionSnapshot& Snapshot = Subsystem->GetSnapshot();
	const FARPose3D& Pose = Snapshot.TrackedPose3D;
	const FTransform RootTransform = Snapshot.TrackedPose3DWorldTransform;
	const FColor Color = SkeletonColor3D.ToFColor(true);

	for (int32 JointIndex = 0; JointIndex < Pose.JointTransforms.Num(); ++JointIndex)
	{
		if (!Pose.IsJointTracked.IsValidIndex(JointIndex) || !Pose.IsJointTracked[JointIndex])
		{
			continue;
		}

		const FVector JointWorld = RootTransform.TransformPosition(Pose.JointTransforms[JointIndex].GetLocation());
		DrawDebugPoint(World, JointWorld, JointPointSize, Color, false, 0.f, SDPG_Foreground);

		const int32 ParentIndex = Pose.SkeletonDefinition.ParentIndices.IsValidIndex(JointIndex)
			? Pose.SkeletonDefinition.ParentIndices[JointIndex]
			: INDEX_NONE;
		if (ParentIndex < 0 || !Pose.IsJointTracked.IsValidIndex(ParentIndex) || !Pose.IsJointTracked[ParentIndex])
		{
			continue;
		}

		const FVector ParentWorld = RootTransform.TransformPosition(Pose.JointTransforms[ParentIndex].GetLocation());
		DrawDebugLine(World, ParentWorld, JointWorld, Color, false, 0.f, SDPG_Foreground, LineThickness);
	}
}

int32 USCARBodyDebugDrawComponent::FindPrimaryVisionTargetIndex(const TArray<FSCARScreenSpaceBodyTarget>& Targets) const
{
	int32 BestIndex = INDEX_NONE;
	float BestScore = -BIG_NUMBER;
	for (int32 TargetIndex = 0; TargetIndex < Targets.Num(); ++TargetIndex)
	{
		const FSCARScreenSpaceBodyTarget& Target = Targets[TargetIndex];
		const FVector2D Center(
			(Target.Bounds.X + Target.Bounds.Z) * 0.5f,
			(Target.Bounds.Y + Target.Bounds.W) * 0.5f);
		const float DistanceFromCenter = FVector2D::Distance(Center, FVector2D(0.5f, 0.5f));
		const float Score = Target.MeanConfidence - DistanceFromCenter * 0.5f;
		if (Score > BestScore)
		{
			BestScore = Score;
			BestIndex = TargetIndex;
		}
	}
	return BestIndex;
}

bool USCARBodyDebugDrawComponent::VisionJointToGuiPixels(
	const FSCARVisionBodyJoint& Joint,
	const int32 ScreenWidth,
	const int32 ScreenHeight,
	FVector2D& OutGuiPixels) const
{
	if (!Joint.bIsValid)
	{
		return false;
	}

	FVector2D ImageUV = Joint.NormalizedPosition;
	if (bFlipVisionY)
	{
		ImageUV.Y = 1.f - ImageUV.Y;
	}

	FVector2D Viewport01;
	if (!SCARBodyScreenMapping::MapImageNormalizedToViewport01(ImageUV, Viewport01))
	{
		return false;
	}

	OutGuiPixels = FVector2D(Viewport01.X * ScreenWidth, Viewport01.Y * ScreenHeight);
	return true;
}
