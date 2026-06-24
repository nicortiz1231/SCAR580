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

namespace SCARBodyDebugDraw
{
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
}

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
		ClearScreenOverlayCache();
		return;
	}

	const USCARBodyDetectionSubsystem* Subsystem = World->GetSubsystem<USCARBodyDetectionSubsystem>();
	if (!Subsystem || !Subsystem->IsPersonInCameraPreview())
	{
		ClearScreenOverlayCache();
		return;
	}

	const bool bCanDraw3D = bDraw3DSkeleton && Subsystem->Has3DBody();
	const bool bCanDrawPose2D = bDrawPose2D && Subsystem->HasPose2D();
	const bool bCanDrawVision = bDrawVisionSkeleton && Subsystem->HasVisionTarget();

	if (SourceMode == ESCARBodyDebugSourceMode::ARKit3D)
	{
		ClearScreenOverlayCache();
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

	ClearScreenOverlayCache();

	if (SourceMode == ESCARBodyDebugSourceMode::Auto)
	{
		if (bCanDrawPose2D)
		{
			AppendPose2DScreenSkeleton(Subsystem);
		}
		else if (bCanDraw3D)
		{
			AppendPose3DProjectedScreenSkeleton(Subsystem);
		}

		if (bCanDrawVision)
		{
			AppendAllVisionScreenSkeletons(Subsystem);
		}

		bHasScreenOverlay = CachedScreenSkeletons.Num() > 0;
		return;
	}

	if (SourceMode == ESCARBodyDebugSourceMode::Pose2D)
	{
		if (bCanDrawPose2D)
		{
			AppendPose2DScreenSkeleton(Subsystem);
		}
		bHasScreenOverlay = CachedScreenSkeletons.Num() > 0;
		return;
	}

	if (SourceMode == ESCARBodyDebugSourceMode::Vision)
	{
		if (bCanDrawVision)
		{
			AppendAllVisionScreenSkeletons(Subsystem);
		}
		bHasScreenOverlay = CachedScreenSkeletons.Num() > 0;
	}
}

void USCARBodyDebugDrawComponent::ClearScreenOverlayCache()
{
	CachedScreenSkeletons.Reset();
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
	ClearScreenOverlayCache();

	if (bDrawPose2D && Subsystem->HasPose2D())
	{
		AppendPose2DScreenSkeleton(Subsystem);
	}

	if (bDrawVisionSkeleton && Subsystem->HasVisionTarget())
	{
		AppendAllVisionScreenSkeletons(Subsystem);
	}

	bHasScreenOverlay = CachedScreenSkeletons.Num() > 0;
}

void USCARBodyDebugDrawComponent::AppendPose2DScreenSkeleton(const USCARBodyDetectionSubsystem* Subsystem)
{
	APlayerController* PlayerController = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
	if (!PlayerController || !Subsystem->HasPose2D())
	{
		return;
	}

	int32 ScreenWidth = 0;
	int32 ScreenHeight = 0;
	PlayerController->GetViewportSize(ScreenWidth, ScreenHeight);
	if (ScreenWidth <= 0 || ScreenHeight <= 0)
	{
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
		return;
	}

	const FARPose2D& Pose2D = Poses2D[BestPoseIndex];
	FSCARBodyDebugScreenSkeleton Skeleton;
	Skeleton.BoneColor = SkeletonColorPose2D;
	Skeleton.JointColor = JointMarkerColor;
	Skeleton.Joints.SetNum(Pose2D.JointLocations.Num());

	for (int32 JointIndex = 0; JointIndex < Pose2D.JointLocations.Num(); ++JointIndex)
	{
		FSCARBodyDebugScreenJoint& Joint = Skeleton.Joints[JointIndex];
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
			|| !Skeleton.Joints.IsValidIndex(JointIndex)
			|| !Skeleton.Joints.IsValidIndex(ParentIndex)
			|| !Skeleton.Joints[JointIndex].bIsValid
			|| !Skeleton.Joints[ParentIndex].bIsValid)
		{
			continue;
		}

		Skeleton.BonePairs.Add(FIntPoint(JointIndex, ParentIndex));
	}

	if (Skeleton.BonePairs.Num() > 0
		|| Skeleton.Joints.ContainsByPredicate([](const FSCARBodyDebugScreenJoint& Joint)
		{
			return Joint.bIsValid;
		}))
	{
		CachedScreenSkeletons.Add(MoveTemp(Skeleton));
	}
}

void USCARBodyDebugDrawComponent::AppendAllVisionScreenSkeletons(const USCARBodyDetectionSubsystem* Subsystem)
{
	APlayerController* PlayerController = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
	if (!PlayerController || !Subsystem->HasVisionTarget())
	{
		return;
	}

	int32 ScreenWidth = 0;
	int32 ScreenHeight = 0;
	PlayerController->GetViewportSize(ScreenWidth, ScreenHeight);
	if (ScreenWidth <= 0 || ScreenHeight <= 0)
	{
		return;
	}

	const TArray<FSCARScreenSpaceBodyTarget>& VisionTargets = Subsystem->GetSnapshot().VisionTargets;
	for (const FSCARScreenSpaceBodyTarget& Target : VisionTargets)
	{
		FSCARBodyDebugScreenSkeleton Skeleton;
		if (!BuildVisionScreenSkeleton(Target, ScreenWidth, ScreenHeight, Skeleton))
		{
			continue;
		}

		CachedScreenSkeletons.Add(MoveTemp(Skeleton));
	}
}

bool USCARBodyDebugDrawComponent::BuildVisionScreenSkeleton(
	const FSCARScreenSpaceBodyTarget& Target,
	const int32 ScreenWidth,
	const int32 ScreenHeight,
	FSCARBodyDebugScreenSkeleton& OutSkeleton) const
{
	OutSkeleton = FSCARBodyDebugScreenSkeleton();
	OutSkeleton.BoneColor = SkeletonColorVision;
	OutSkeleton.JointColor = JointMarkerColor;
	OutSkeleton.Joints.SetNum(FSCARScreenSpaceBodyTarget::JointCount);

	for (int32 JointIndex = 0; JointIndex < Target.Joints.Num(); ++JointIndex)
	{
		FSCARBodyDebugScreenJoint& Joint = OutSkeleton.Joints[JointIndex];
		Joint.bIsValid = false;

		FVector2D GuiPixels;
		if (!VisionJointToGuiPixels(Target.Joints[JointIndex], ScreenWidth, ScreenHeight, GuiPixels))
		{
			continue;
		}

		Joint.GuiPosition = GuiPixels;
		Joint.bIsValid = true;
	}

	for (const TPair<int32, int32>& BonePair : SCARBodyDebugDraw::VisionBonePairs)
	{
		if (!OutSkeleton.Joints.IsValidIndex(BonePair.Key)
			|| !OutSkeleton.Joints.IsValidIndex(BonePair.Value)
			|| !OutSkeleton.Joints[BonePair.Key].bIsValid
			|| !OutSkeleton.Joints[BonePair.Value].bIsValid)
		{
			continue;
		}

		OutSkeleton.BonePairs.Add(FIntPoint(BonePair.Key, BonePair.Value));
	}

	return OutSkeleton.BonePairs.Num() > 0;
}

void USCARBodyDebugDrawComponent::AppendPose3DProjectedScreenSkeleton(const USCARBodyDetectionSubsystem* Subsystem)
{
	APlayerController* PlayerController = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
	if (!PlayerController || !Subsystem->Has3DBody())
	{
		return;
	}

	int32 ScreenWidth = 0;
	int32 ScreenHeight = 0;
	PlayerController->GetViewportSize(ScreenWidth, ScreenHeight);
	if (ScreenWidth <= 0 || ScreenHeight <= 0)
	{
		return;
	}

	const FSCARBodyDetectionSnapshot& Snapshot = Subsystem->GetSnapshot();
	const FARPose3D& Pose = Snapshot.TrackedPose3D;
	const FTransform RootTransform = Snapshot.TrackedPose3DWorldTransform;

	FSCARBodyDebugScreenSkeleton Skeleton;
	Skeleton.BoneColor = SkeletonColor3D;
	Skeleton.JointColor = JointMarkerColor;
	Skeleton.Joints.SetNum(Pose.JointTransforms.Num());

	for (int32 JointIndex = 0; JointIndex < Pose.JointTransforms.Num(); ++JointIndex)
	{
		FSCARBodyDebugScreenJoint& Joint = Skeleton.Joints[JointIndex];
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
			|| !Skeleton.Joints.IsValidIndex(JointIndex)
			|| !Skeleton.Joints.IsValidIndex(ParentIndex)
			|| !Skeleton.Joints[JointIndex].bIsValid
			|| !Skeleton.Joints[ParentIndex].bIsValid)
		{
			continue;
		}

		Skeleton.BonePairs.Add(FIntPoint(JointIndex, ParentIndex));
	}

	if (Skeleton.BonePairs.Num() > 0)
	{
		CachedScreenSkeletons.Add(MoveTemp(Skeleton));
	}
}

void USCARBodyDebugDrawComponent::DrawScreenOverlay(UCanvas* Canvas) const
{
	for (const FSCARBodyDebugScreenSkeleton& Skeleton : CachedScreenSkeletons)
	{
		for (const FIntPoint& BonePair : Skeleton.BonePairs)
		{
			if (!Skeleton.Joints.IsValidIndex(BonePair.X) || !Skeleton.Joints.IsValidIndex(BonePair.Y))
			{
				continue;
			}

			const FSCARBodyDebugScreenJoint& StartJoint = Skeleton.Joints[BonePair.X];
			const FSCARBodyDebugScreenJoint& EndJoint = Skeleton.Joints[BonePair.Y];
			if (!StartJoint.bIsValid || !EndJoint.bIsValid)
			{
				continue;
			}

			DrawGuiLine(Canvas, StartJoint.GuiPosition, EndJoint.GuiPosition, LineThickness, Skeleton.BoneColor);
		}

		if (!bDrawJointMarkers)
		{
			continue;
		}

		for (const FSCARBodyDebugScreenJoint& Joint : Skeleton.Joints)
		{
			if (!Joint.bIsValid)
			{
				continue;
			}

			DrawGuiJoint(Canvas, Joint.GuiPosition, ScreenJointPixelSize, Skeleton.JointColor);
		}
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
