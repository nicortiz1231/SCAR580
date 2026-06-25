#include "SCARBodyDetectionSubsystem.h"

#include "ARBlueprintLibrary.h"
#include "ARTrackable.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "HAL/PlatformTime.h"
#include "SCARVisionBodyPoseProvider.h"
#include "TimerManager.h"

void USCARBodyDetectionSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	VisionProvider = NewObject<USCARVisionBodyPoseProvider>(this);
}

void USCARBodyDetectionSubsystem::Deinitialize()
{
	VisionProvider = nullptr;
	Super::Deinitialize();
}

void USCARBodyDetectionSubsystem::Tick(const float DeltaTime)
{
	(void)DeltaTime;

	const FARSessionStatus SessionStatus = UARBlueprintLibrary::GetARSessionStatus();
	if (SessionStatus.Status != EARSessionStatus::Running)
	{
		return;
	}

	UpdateArkitBodyTracking();

	if (bEnableVisionMultiBodyDetection && VisionProvider)
	{
		UpdateVisionTracking();
	}

	PublishSnapshot();
}

TStatId USCARBodyDetectionSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(USCARBodyDetectionSubsystem, STATGROUP_Tickables);
}

void USCARBodyDetectionSubsystem::UpdateArkitBodyTracking()
{
	Snapshot.bHas3DBody = false;
	Snapshot.bHasPose2D = false;
	Snapshot.TrackedPoses2D.Reset();

	TArray<UARTrackedGeometry*> Geometries = UARBlueprintLibrary::GetAllGeometriesByClass(UARTrackedPose::StaticClass());
	for (UARTrackedGeometry* Geometry : Geometries)
	{
		UARTrackedPose* TrackedPose = Cast<UARTrackedPose>(Geometry);
		if (!TrackedPose || !TrackedPose->IsTracked())
		{
			continue;
		}

		const FARPose3D& PoseData = TrackedPose->GetTrackedPoseData();
		if (PoseData.JointTransforms.Num() == 0)
		{
			continue;
		}

		Snapshot.bHas3DBody = true;
		Snapshot.TrackedPose3D = PoseData;
		Snapshot.TrackedPose3DWorldTransform = TrackedPose->GetLocalToWorldTransform();
		break;
	}

	const TArray<FARPose2D> Poses2D = UARBlueprintLibrary::GetAllTracked2DPoses();
	if (Poses2D.Num() > 0)
	{
		for (const FARPose2D& Pose2D : Poses2D)
		{
			bool bAnyJointTracked = false;
			for (const bool bTracked : Pose2D.IsJointTracked)
			{
				if (bTracked)
				{
					bAnyJointTracked = true;
					break;
				}
			}

			if (bAnyJointTracked)
			{
				Snapshot.bHasPose2D = true;
				Snapshot.TrackedPoses2D.Add(Pose2D);
			}
		}
	}

	if (Snapshot.bHasPose2D)
	{
		OnPose2DUpdated.Broadcast(Snapshot.TrackedPoses2D);
	}

	if (Snapshot.bHas3DBody && !bHad3DBodyLastFrame)
	{
		OnBodyDetected.Broadcast();
	}
	else if (!Snapshot.bHas3DBody && bHad3DBodyLastFrame)
	{
		OnBodyLost.Broadcast();
	}

	bHad3DBodyLastFrame = Snapshot.bHas3DBody;
	bHadPose2DLastFrame = Snapshot.bHasPose2D;
}

void USCARBodyDetectionSubsystem::UpdateVisionTracking()
{
	UWorld* World = GetWorld();
	if (!World || !VisionProvider || !VisionProvider->IsSupported())
	{
		Snapshot.bHasVisionTarget = false;
		Snapshot.VisionTargets.Reset();
		return;
	}

	if (bVisionDetectionPending)
	{
		return;
	}

	bVisionDetectionPending = true;
	World->GetTimerManager().SetTimerForNextTick(FTimerDelegate::CreateWeakLambda(this, [this]()
	{
		bVisionDetectionPending = false;
		FlushVisionDetection();
	}));
}

void USCARBodyDetectionSubsystem::FlushVisionDetection()
{
	UWorld* World = GetWorld();
	if (!World || !VisionProvider || !VisionProvider->IsSupported())
	{
		return;
	}

	const FARSessionStatus SessionStatus = UARBlueprintLibrary::GetARSessionStatus();
	if (SessionStatus.Status != EARSessionStatus::Running)
	{
		return;
	}

	// Skip vision until AR has produced at least one camera texture — raw ARKit pointers
	// are not safe during the first frames after session start (device crash: objc_msgSend).
	if (!UARBlueprintLibrary::GetARTexture(EARTextureType::CameraImage))
	{
		return;
	}

	VisionProvider->TickDetection(World);
	Snapshot.VisionTargets = VisionProvider->GetTargets();
	Snapshot.bHasVisionTarget = Snapshot.VisionTargets.Num() > 0;

	if (Snapshot.bHasVisionTarget)
	{
		OnVisionTargetsUpdated.Broadcast(Snapshot.VisionTargets);
	}

	if (Snapshot.bHasVisionTarget != bHadVisionTargetLastFrame && Snapshot.bHasVisionTarget)
	{
		OnBodyDetected.Broadcast();
	}
	else if (!Snapshot.bHasVisionTarget && !Snapshot.bHas3DBody && bHadVisionTargetLastFrame)
	{
		OnBodyLost.Broadcast();
	}

	bHadVisionTargetLastFrame = Snapshot.bHasVisionTarget;
	PublishSnapshot();
}

void USCARBodyDetectionSubsystem::PublishSnapshot()
{
	Snapshot.bPersonInCameraPreview = Snapshot.bHas3DBody || Snapshot.bHasPose2D || Snapshot.bHasVisionTarget;
	OnDetectionUpdated.Broadcast(Snapshot);

#if !UE_BUILD_SHIPPING
	if (GEngine && VisionProvider)
	{
		static double LastHudRefreshSeconds = 0.0;
		const double NowSeconds = FPlatformTime::Seconds();
		if (NowSeconds - LastHudRefreshSeconds >= 0.5)
		{
			LastHudRefreshSeconds = NowSeconds;
			const FString HudMessage = FString::Printf(
				TEXT("Vision: %d bodies | cam=%s buf=%s orient=%d | active=%d | Pose2D=%d"),
				VisionProvider->GetDebugLastBodyCount(),
				*VisionProvider->GetDebugLastCameraSource(),
				VisionProvider->GetDebugHadCameraBuffer() ? TEXT("Y") : TEXT("N"),
				VisionProvider->GetDebugLastOrientation(),
				Snapshot.VisionTargets.Num(),
				Snapshot.TrackedPoses2D.Num());
			GEngine->AddOnScreenDebugMessage(74501, 0.55f, FColor::Cyan, HudMessage);
		}
	}
#endif
}
