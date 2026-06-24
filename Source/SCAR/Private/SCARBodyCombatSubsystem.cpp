#include "SCARBodyCombatSubsystem.h"

#include "ARTrackable.h"
#include "Blueprint/UserWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/Image.h"
#include "Debug/DebugDrawService.h"
#include "Engine/Canvas.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "SCARBodyDetectionSubsystem.h"
#include "SCARBodyHitFeedbackActor.h"
#include "SCARScreenSpaceBodyTargeting.h"
#include "SCARBodyScreenMapping.h"
#include "Engine/Texture2D.h"
#include "Sound/SoundBase.h"
#include "UObject/UnrealType.h"

namespace SCARBodyCombatFeedback
{
	static UUserWidget* FindCharacterHudWidget(const APawn* Pawn)
	{
		if (!Pawn)
		{
			return nullptr;
		}

		static const FName HudPropertyName(TEXT("HUD"));
		if (const FObjectPropertyBase* HudProperty = FindFProperty<FObjectPropertyBase>(
			Pawn->GetClass(),
			HudPropertyName))
		{
			if (UObject* HudObject = HudProperty->GetObjectPropertyValue_InContainer(Pawn))
			{
				return Cast<UUserWidget>(HudObject);
			}
		}

		return nullptr;
	}

	static void PlayHudCustomEvent(UUserWidget* HudWidget, const FName EventName)
	{
		if (!HudWidget)
		{
			return;
		}

		if (UFunction* EventFunction = HudWidget->FindFunction(EventName))
		{
			HudWidget->ProcessEvent(EventFunction, nullptr);
		}
	}

	static UImage* FindHudHitMarkerImageWidget(UUserWidget* HudWidget)
	{
		if (!HudWidget || !HudWidget->WidgetTree)
		{
			return nullptr;
		}

		static const FName HitMarkerWidgetName(TEXT("Hitmarker"));
		if (UWidget* Widget = HudWidget->WidgetTree->FindWidget(HitMarkerWidgetName))
		{
			return Cast<UImage>(Widget);
		}

		return nullptr;
	}

	static void EnsureWidgetChainVisible(UWidget* Widget)
	{
		while (Widget)
		{
			const ESlateVisibility Visibility = Widget->GetVisibility();
			if (Visibility == ESlateVisibility::Collapsed || Visibility == ESlateVisibility::Hidden)
			{
				Widget->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
			}

			Widget = Widget->GetParent();
		}
	}
}

USCARBodyCombatSubsystem::FTargetHealthState& USCARBodyCombatSubsystem::GetOrCreateHealth(const int32 TargetId)
{
	FTargetHealthState& State = HealthByTargetId.FindOrAdd(TargetId);
	if (State.Health <= 0.f)
	{
		State.Health = MaxHealth;
	}

	return State;
}

void USCARBodyCombatSubsystem::ResetTargetHealth(const int32 TargetId)
{
	FTargetHealthState& State = GetOrCreateHealth(TargetId);
	State.Health = MaxHealth;
	State.DeadUntilSeconds = 0.0;
}

bool USCARBodyCombatSubsystem::BuildAimSamples(
	const USCARBodyDetectionSubsystem* DetectionSubsystem,
	APlayerController* PlayerController,
	TArray<SCARScreenSpaceBodyTargeting::FSCARScreenSpaceAimSample>& OutSamples) const
{
	OutSamples.Reset();
	if (!DetectionSubsystem || !PlayerController)
	{
		return false;
	}

	const FSCARBodyDetectionSnapshot& Snapshot = DetectionSubsystem->GetSnapshot();

	for (const FSCARScreenSpaceBodyTarget& Target : Snapshot.VisionTargets)
	{
		SCARScreenSpaceBodyTargeting::FSCARScreenSpaceAimSample Sample;
		if (SCARScreenSpaceBodyTargeting::BuildVisionAimSample(Target, Sample))
		{
			OutSamples.Add(Sample);
		}
	}

	if (OutSamples.Num() == 0 && Snapshot.bHasPose2D)
	{
		int32 BestPoseIndex = INDEX_NONE;
		int32 MostTrackedJoints = -1;
		for (int32 PoseIndex = 0; PoseIndex < Snapshot.TrackedPoses2D.Num(); ++PoseIndex)
		{
			int32 TrackedCount = 0;
			for (const bool bTracked : Snapshot.TrackedPoses2D[PoseIndex].IsJointTracked)
			{
				TrackedCount += bTracked ? 1 : 0;
			}

			if (TrackedCount > MostTrackedJoints)
			{
				MostTrackedJoints = TrackedCount;
				BestPoseIndex = PoseIndex;
			}
		}

		if (Snapshot.TrackedPoses2D.IsValidIndex(BestPoseIndex))
		{
			SCARScreenSpaceBodyTargeting::FSCARScreenSpaceAimSample Sample;
			if (SCARScreenSpaceBodyTargeting::BuildPose2DAimSample(
				Snapshot.TrackedPoses2D[BestPoseIndex],
				PlayerController,
				bFlipPose2DY,
				bUseImageSpacePose2DMapping,
				0,
				Sample))
			{
				OutSamples.Add(Sample);
			}
		}
	}

	return OutSamples.Num() > 0;
}

bool USCARBodyCombatSubsystem::TryGetTrackedHitViewport01(
	const int32 TargetId,
	const ESCARVisionBodyJoint AnchorJointA,
	const ESCARVisionBodyJoint AnchorJointB,
	const float BoneT,
	FVector2D& OutViewport01) const
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return false;
	}

	const USCARBodyDetectionSubsystem* DetectionSubsystem = World->GetSubsystem<USCARBodyDetectionSubsystem>();
	APlayerController* PlayerController = World->GetFirstPlayerController();
	if (!DetectionSubsystem || !PlayerController)
	{
		return false;
	}

	const FSCARBodyDetectionSnapshot& Snapshot = DetectionSubsystem->GetSnapshot();
	if (SCARScreenSpaceBodyTargeting::TryGetTrackedHitViewport01FromVision(
		Snapshot.VisionTargets,
		TargetId,
		AnchorJointA,
		AnchorJointB,
		BoneT,
		OutViewport01))
	{
		return true;
	}

	TArray<SCARScreenSpaceBodyTargeting::FSCARScreenSpaceAimSample> Samples;
	if (!BuildAimSamples(DetectionSubsystem, PlayerController, Samples))
	{
		return false;
	}

	const int32 JointIndex = static_cast<int32>(AnchorJointA);
	for (const SCARScreenSpaceBodyTargeting::FSCARScreenSpaceAimSample& Sample : Samples)
	{
		if (Sample.TargetId != TargetId)
		{
			continue;
		}

		if (!Sample.JointImageUV.IsValidIndex(JointIndex)
			|| !Sample.JointValid.IsValidIndex(JointIndex)
			|| !Sample.JointValid[JointIndex])
		{
			continue;
		}

		FVector2D ImageA = Sample.JointImageUV[JointIndex];
		FVector2D ImageB = ImageA;
		if (const int32 IndexB = static_cast<int32>(AnchorJointB);
			Sample.JointImageUV.IsValidIndex(IndexB)
			&& Sample.JointValid.IsValidIndex(IndexB)
			&& Sample.JointValid[IndexB])
		{
			ImageB = Sample.JointImageUV[IndexB];
		}

		const FVector2D HitImageUV = FMath::Lerp(ImageA, ImageB, FMath::Clamp(BoneT, 0.f, 1.f));
		if (SCARBodyScreenMapping::MapImageNormalizedToViewport01(HitImageUV, OutViewport01))
		{
			return true;
		}
	}

	return false;
}

FVector2D USCARBodyCombatSubsystem::GetCombatAimViewport01(const UObject* WorldContextObject)
{
	const UWorld* World = GEngine
		? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::LogAndReturnNull)
		: nullptr;
	if (!World)
	{
		return FVector2D(0.5f, 0.5f);
	}

	if (const APlayerController* PlayerController = World->GetFirstPlayerController())
	{
		int32 SizeX = 0;
		int32 SizeY = 0;
		PlayerController->GetViewportSize(SizeX, SizeY);
		if (SizeX > 0 && SizeY > 0)
		{
			float MouseX = 0.f;
			float MouseY = 0.f;
			if (PlayerController->GetMousePosition(MouseX, MouseY))
			{
				return FVector2D(MouseX / SizeX, MouseY / SizeY);
			}
		}
	}

	return FVector2D(0.5f, 0.5f);
}

FSCARBodyCombatHitResult USCARBodyCombatSubsystem::TryApplyShot(
	const UObject* WorldContextObject,
	const float BaseDamage,
	const float CriticalMultiplier,
	const bool bRequirePersonInPreview)
{
	return TryApplyShotAtViewport(
		WorldContextObject,
		GetCombatAimViewport01(WorldContextObject),
		BaseDamage,
		CriticalMultiplier,
		bRequirePersonInPreview);
}

FSCARBodyCombatHitResult USCARBodyCombatSubsystem::TryApplyShotAtViewport(
	const UObject* WorldContextObject,
	const FVector2D& AimViewport01,
	const float BaseDamage,
	const float CriticalMultiplier,
	const bool bRequirePersonInPreview)
{
	FSCARBodyCombatHitResult Result;
	UWorld* World = GEngine
		? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::LogAndReturnNull)
		: nullptr;
	if (!World)
	{
		return Result;
	}

	USCARBodyDetectionSubsystem* DetectionSubsystem = World->GetSubsystem<USCARBodyDetectionSubsystem>();
	APlayerController* PlayerController = World->GetFirstPlayerController();
	if (!DetectionSubsystem || !PlayerController)
	{
		return Result;
	}

	if (bRequirePersonInPreview && !DetectionSubsystem->IsPersonInCameraPreview())
	{
		return Result;
	}

	TArray<SCARScreenSpaceBodyTargeting::FSCARScreenSpaceAimSample> Samples;
	if (!BuildAimSamples(DetectionSubsystem, PlayerController, Samples))
	{
		return Result;
	}

	const double NowSeconds = FPlatformTime::Seconds();
	int32 BestTargetIndex = INDEX_NONE;
	bool bIsHeadshot = false;
	if (!SCARScreenSpaceBodyTargeting::TryGetBestTarget(
		Samples,
		AimViewport01,
		MaxBoneDistanceNormalized,
		BoundsPaddingNormalized,
		HeadRegionScale,
		TorsoRegionScale,
		LegRegionScale,
		MaxTargetAgeSeconds,
		NowSeconds,
		BestTargetIndex,
		bIsHeadshot))
	{
		return Result;
	}

	const SCARScreenSpaceBodyTargeting::FSCARScreenSpaceAimSample& BestSample = Samples[BestTargetIndex];
	FTargetHealthState& HealthState = GetOrCreateHealth(BestSample.TargetId);
	if (HealthState.DeadUntilSeconds > NowSeconds)
	{
		return Result;
	}

	if (HealthState.Health <= 0.f)
	{
		HealthState.Health = MaxHealth;
	}

	float AppliedDamage = FMath::Max(1.f, BaseDamage);
	if (bIsHeadshot)
	{
		AppliedDamage *= FMath::Max(1.f, CriticalMultiplier);
	}

	HealthState.Health -= AppliedDamage;

	FVector2D HitImageUV = FVector2D::ZeroVector;
	ESCARVisionBodyJoint AnchorJointA = ESCARVisionBodyJoint::Root;
	ESCARVisionBodyJoint AnchorJointB = ESCARVisionBodyJoint::Root;
	float AnchorBoneT = 0.f;
	SCARScreenSpaceBodyTargeting::ResolveHitBoneAnchorOnSample(
		BestSample,
		AimViewport01,
		HitImageUV,
		AnchorJointA,
		AnchorJointB,
		AnchorBoneT);
	const ESCARVisionBodyJoint HitJoint = AnchorJointA;

	FVector2D HitViewport01 = AimViewport01;
	if (!SCARBodyScreenMapping::MapImageNormalizedToViewport01(HitImageUV, HitViewport01))
	{
		ESCARVisionBodyJoint FallbackJoint = AnchorJointA;
		SCARScreenSpaceBodyTargeting::ResolveHitViewportOnSample(BestSample, AimViewport01, HitViewport01, FallbackJoint);
	}

	FVector HitWorldLocation = FVector::ZeroVector;
	SCARScreenSpaceBodyTargeting::Viewport01ToWorldAtDistance(
		PlayerController,
		HitViewport01,
		HitWorldDepthCentimeters,
		HitWorldLocation);

	Result.bHit = true;
	Result.bIsHeadshot = bIsHeadshot;
	Result.TargetId = BestSample.TargetId;
	Result.HitJoint = HitJoint;
	Result.HitViewport01 = HitViewport01;
	Result.HitImageUV = HitImageUV;
	Result.HitAnchorJointA = AnchorJointA;
	Result.HitAnchorJointB = AnchorJointB;
	Result.HitAnchorBoneT = AnchorBoneT;
	Result.HitWorldLocation = HitWorldLocation;
	Result.AppliedDamage = AppliedDamage;
	Result.RemainingHealth = FMath::Max(0.f, HealthState.Health);
	Result.HitRegion = bIsHeadshot
		? ESCARBodyHitRegion::Head
		: (HitJoint == ESCARVisionBodyJoint::LeftKnee
			|| HitJoint == ESCARVisionBodyJoint::RightKnee
			|| HitJoint == ESCARVisionBodyJoint::LeftAnkle
			|| HitJoint == ESCARVisionBodyJoint::RightAnkle
			|| HitJoint == ESCARVisionBodyJoint::LeftHip
			|| HitJoint == ESCARVisionBodyJoint::RightHip
			? ESCARBodyHitRegion::Legs
			: ESCARBodyHitRegion::Torso);
	Result.HitMarkerScreenSizePx = SCARScreenSpaceBodyTargeting::ComputeHitRegionScreenDiameter(
		BestSample,
		Result.HitRegion,
		PlayerController);

	const int32 HitJointIndex = static_cast<int32>(HitJoint);
	if (BestSample.JointImageUV.IsValidIndex(HitJointIndex)
		&& BestSample.JointValid.IsValidIndex(HitJointIndex)
		&& BestSample.JointValid[HitJointIndex])
	{
		Result.HitMarkerJointOffset = HitImageUV - BestSample.JointImageUV[HitJointIndex];
	}

	if (HealthState.Health <= 0.f)
	{
		Result.bKilledTarget = true;
		HealthState.DeadUntilSeconds = RespawnDelaySeconds > 0.f ? NowSeconds + RespawnDelaySeconds : 0.0;
	}

	SpawnHitFeedback(Result);
	OnBodyHit.Broadcast(Result);
	return Result;
}

void USCARBodyCombatSubsystem::EnsureFeedbackAssets()
{
	if (!HitMarkerTexture)
	{
		HitMarkerTexture = LoadObject<UTexture2D>(
			nullptr,
			TEXT("/Game/BodycamFPSKIT/Blueprints/Widgets/T_HitMarker.T_HitMarker"));
		HeadshotMarkerTexture = HitMarkerTexture;
	}

	if (!CachedHitSound)
	{
		CachedHitSound = LoadObject<USoundBase>(
			nullptr,
			TEXT("/Game/BodycamFPSKIT/Audio/Character/HitMarker.HitMarker"));
	}
}

ASCARBodyHitFeedbackActor* USCARBodyCombatSubsystem::EnsureBloodFeedbackActor()
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return nullptr;
	}

	if (!PooledBloodFeedbackActor)
	{
		FActorSpawnParameters SpawnParams;
		SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		SpawnParams.ObjectFlags |= RF_Transient;
		PooledBloodFeedbackActor = World->SpawnActor<ASCARBodyHitFeedbackActor>(
			ASCARBodyHitFeedbackActor::StaticClass(),
			FVector::ZeroVector,
			FRotator::ZeroRotator,
			SpawnParams);
	}

	return PooledBloodFeedbackActor;
}

void USCARBodyCombatSubsystem::InvalidateHudCache()
{
	CachedHudWidget.Reset();
	CachedHudHitMarkerImage.Reset();
	CachedHudPawn.Reset();
	bUseCanvasHitMarkerFallback = false;
}

void USCARBodyCombatSubsystem::SpawnHitFeedback(const FSCARBodyCombatHitResult& HitResult)
{
	if (!HitResult.bHit)
	{
		return;
	}

	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	if (bUseBodycamHudHitMarker)
	{
		const APlayerController* PlayerController = World->GetFirstPlayerController();
		const APawn* Pawn = PlayerController ? PlayerController->GetPawn() : nullptr;
		if (UUserWidget* HudWidget = SCARBodyCombatFeedback::FindCharacterHudWidget(Pawn))
		{
			SCARBodyCombatFeedback::PlayHudCustomEvent(
				HudWidget,
				HitResult.bKilledTarget ? FName(TEXT("HitMarkerDead")) : FName(TEXT("HitmarkerEffect")));
		}
	}

	if (bSpawnWorldHitMarkers)
	{
		ShowSkeletonHitMarker(HitResult);
	}

	if (bPlayHitSound)
	{
		EnsureFeedbackAssets();
		const double NowSeconds = FPlatformTime::Seconds();
		if (CachedHitSound
			&& (LastHitSoundPlaySeconds < 0.0
				|| NowSeconds - LastHitSoundPlaySeconds >= static_cast<double>(MinHitSoundIntervalSeconds)))
		{
			LastHitSoundPlaySeconds = NowSeconds;
			if (APlayerController* PlayerController = World->GetFirstPlayerController())
			{
				UGameplayStatics::PlaySound2D(PlayerController, CachedHitSound);
			}
		}
	}

	if (bSpawnBloodEffect)
	{
		if (ASCARBodyHitFeedbackActor* BloodActor = EnsureBloodFeedbackActor())
		{
			BloodActor->ActivateAtLocation(HitResult.HitWorldLocation);
		}
	}
}

void USCARBodyCombatSubsystem::Deinitialize()
{
	HideSkeletonHitMarker();
	InvalidateHudCache();

	if (PooledBloodFeedbackActor)
	{
		PooledBloodFeedbackActor->Destroy();
		PooledBloodFeedbackActor = nullptr;
	}

	Super::Deinitialize();
}

void USCARBodyCombatSubsystem::Tick(const float DeltaTime)
{
	if (!bSkeletonHitMarkerVisible)
	{
		return;
	}

	SkeletonHitMarkerHideRemaining -= DeltaTime;
	if (SkeletonHitMarkerHideRemaining <= 0.f)
	{
		HideSkeletonHitMarker();
		return;
	}

	UpdateSkeletonHitMarkerOverlay();
}

TStatId USCARBodyCombatSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(USCARBodyCombatSubsystem, STATGROUP_Tickables);
}

bool USCARBodyCombatSubsystem::IsTickable() const
{
	return bSkeletonHitMarkerVisible && GetWorld() != nullptr && !IsTemplate();
}

UImage* USCARBodyCombatSubsystem::FindHudHitMarkerImage() const
{
	if (CachedHudHitMarkerImage.IsValid())
	{
		return CachedHudHitMarkerImage.Get();
	}

	UWorld* World = GetWorld();
	if (!World)
	{
		return nullptr;
	}

	const APlayerController* PlayerController = World->GetFirstPlayerController();
	const APawn* Pawn = PlayerController ? PlayerController->GetPawn() : nullptr;
	if (CachedHudPawn.IsValid() && CachedHudPawn.Get() != Pawn)
	{
		CachedHudWidget.Reset();
		CachedHudHitMarkerImage.Reset();
		CachedHudPawn.Reset();
	}

	UUserWidget* HudWidget = SCARBodyCombatFeedback::FindCharacterHudWidget(Pawn);
	if (HudWidget)
	{
		CachedHudWidget = HudWidget;
		CachedHudPawn = Pawn;
	}

	UImage* HitMarkerImage = SCARBodyCombatFeedback::FindHudHitMarkerImageWidget(HudWidget);
	if (HitMarkerImage)
	{
		CachedHudHitMarkerImage = HitMarkerImage;
	}

	return HitMarkerImage;
}

bool USCARBodyCombatSubsystem::ApplyHudHitMarkerLayout(
	UImage* HitMarkerImage,
	const FVector2D& Viewport01,
	const float SizePx)
{
	if (!HitMarkerImage)
	{
		return false;
	}

	UWorld* World = GetWorld();
	APlayerController* PlayerController = World ? World->GetFirstPlayerController() : nullptr;
	if (!PlayerController)
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

	const float ClampedSize = FMath::Clamp(SizePx, 12.f, 36.f);
	const FVector2D Center(
		Viewport01.X * static_cast<float>(ScreenWidth),
		Viewport01.Y * static_cast<float>(ScreenHeight));

	if (UCanvasPanelSlot* CanvasSlot = Cast<UCanvasPanelSlot>(HitMarkerImage->Slot))
	{
		CanvasSlot->SetAnchors(FAnchors(0.f, 0.f, 0.f, 0.f));
		CanvasSlot->SetAlignment(FVector2D(0.5f, 0.5f));
		CanvasSlot->SetAutoSize(false);
		CanvasSlot->SetPosition(Center);
		CanvasSlot->SetSize(FVector2D(ClampedSize, ClampedSize));
	}

	if (!HitMarkerTexture)
	{
		EnsureFeedbackAssets();
	}

	if (UTexture2D* Texture = bMarkerHeadshot ? HeadshotMarkerTexture.Get() : HitMarkerTexture.Get())
	{
		FSlateBrush Brush = HitMarkerImage->GetBrush();
		Brush.SetResourceObject(Texture);
		Brush.ImageSize = FVector2D(ClampedSize, ClampedSize);
		Brush.DrawAs = ESlateBrushDrawType::Image;
		HitMarkerImage->SetBrush(Brush);
	}

	HitMarkerImage->SetColorAndOpacity(FLinearColor::White);
	HitMarkerImage->SetRenderOpacity(1.f);
	SCARBodyCombatFeedback::EnsureWidgetChainVisible(HitMarkerImage);
	HitMarkerImage->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
	return true;
}

void USCARBodyCombatSubsystem::DrawSkeletonHitMarkerOverlay(
	UCanvas* Canvas,
	APlayerController* PlayerController)
{
	if (!bSkeletonHitMarkerVisible || !Canvas || !PlayerController)
	{
		return;
	}

	if (FindHudHitMarkerImage() && !bUseCanvasHitMarkerFallback)
	{
		return;
	}

	if (!HitMarkerTexture)
	{
		EnsureFeedbackAssets();
	}

	UTexture2D* Texture = bMarkerHeadshot ? HeadshotMarkerTexture.Get() : HitMarkerTexture.Get();
	if (!Texture)
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

	const float ClampedSize = FMath::Clamp(MarkerScreenSizePx, 12.f, 36.f);
	const FVector2D Center(
		FallbackHitViewport01.X * static_cast<float>(ScreenWidth),
		FallbackHitViewport01.Y * static_cast<float>(ScreenHeight));
	const FVector2D TopLeft(Center.X - ClampedSize * 0.5f, Center.Y - ClampedSize * 0.5f);

	Canvas->K2_DrawTexture(
		Texture,
		TopLeft,
		FVector2D(ClampedSize, ClampedSize),
		FVector2D::ZeroVector,
		FVector2D::UnitVector,
		FLinearColor::White,
		BLEND_Translucent);
}

void USCARBodyCombatSubsystem::ShowSkeletonHitMarker(const FSCARBodyCombatHitResult& HitResult)
{
	const bool bWasVisible = bSkeletonHitMarkerVisible;

	TrackedTargetId = HitResult.TargetId;
	TrackedAnchorJointA = HitResult.HitAnchorJointA;
	TrackedAnchorJointB = HitResult.HitAnchorJointB;
	TrackedBoneT = HitResult.HitAnchorBoneT;
	FallbackHitImageUV = HitResult.HitImageUV;
	FallbackHitViewport01 = HitResult.HitViewport01;
	MarkerScreenSizePx = FMath::Clamp(HitResult.HitMarkerScreenSizePx, 12.f, 36.f);
	bMarkerHeadshot = HitResult.bIsHeadshot;
	bSkeletonHitMarkerVisible = true;
	SkeletonHitMarkerHideRemaining = HitMarkerVisibleSeconds;

	if (!bWasVisible)
	{
		InvalidateHudCache();
	}

	if (!bWasVisible && bPlayHudHitMarkerBlink)
	{
		UWorld* World = GetWorld();
		const APlayerController* PlayerController = World ? World->GetFirstPlayerController() : nullptr;
		const APawn* Pawn = PlayerController ? PlayerController->GetPawn() : nullptr;
		if (UUserWidget* HudWidget = SCARBodyCombatFeedback::FindCharacterHudWidget(Pawn))
		{
			SCARBodyCombatFeedback::PlayHudCustomEvent(
				HudWidget,
				HitResult.bKilledTarget ? FName(TEXT("HitMarkerDead")) : FName(TEXT("HitmarkerEffect")));
		}
	}

	UpdateSkeletonHitMarkerOverlay();
}

void USCARBodyCombatSubsystem::HideSkeletonHitMarker()
{
	bSkeletonHitMarkerVisible = false;
	SkeletonHitMarkerHideRemaining = 0.f;
	bUseCanvasHitMarkerFallback = false;

	if (UImage* HitMarkerImage = FindHudHitMarkerImage())
	{
		HitMarkerImage->SetVisibility(ESlateVisibility::Hidden);
	}
}

void USCARBodyCombatSubsystem::UpdateSkeletonHitMarkerOverlay()
{
	if (!bSkeletonHitMarkerVisible)
	{
		return;
	}

	FVector2D Viewport01 = FallbackHitViewport01;
	if (!TryGetTrackedHitViewport01(
		TrackedTargetId,
		TrackedAnchorJointA,
		TrackedAnchorJointB,
		TrackedBoneT,
		Viewport01))
	{
		if (!SCARBodyScreenMapping::MapImageNormalizedToViewport01(FallbackHitImageUV, Viewport01))
		{
			Viewport01 = FallbackHitViewport01;
		}
	}
	else
	{
		FallbackHitViewport01 = Viewport01;
	}

	if (UImage* HitMarkerImage = FindHudHitMarkerImage())
	{
		bUseCanvasHitMarkerFallback = !ApplyHudHitMarkerLayout(HitMarkerImage, Viewport01, MarkerScreenSizePx);
	}
	else
	{
		bUseCanvasHitMarkerFallback = true;
	}
}
