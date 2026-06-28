#pragma once

#include "CoreMinimal.h"
#include "SCARBodyCombatTypes.h"
#include "SCARScreenSpaceBodyTargeting.h"
#include "Subsystems/WorldSubsystem.h"
#include "SCARBodyCombatSubsystem.generated.h"

class APlayerController;
class ASCARBodyHitFeedbackActor;
class UCanvas;
class UImage;
class USCARBodyDetectionSubsystem;
class USoundBase;
class UTexture2D;
class UUserWidget;

UCLASS()
class SCAR_API USCARBodyCombatSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	UPROPERTY(BlueprintAssignable, Category = "SCAR|Body Combat")
	FSCARBodyCombatHitDelegate OnBodyHit;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Combat|Thresholds")
	float MaxBoneDistanceNormalized = 0.08f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Combat|Thresholds")
	float BoundsPaddingNormalized = 0.03f;

	/** Expands the detected body bounding box by this fraction of its width/height on each side. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Combat|Thresholds", meta = (ClampMin = "0.0", ClampMax = "0.5"))
	float BodyHitBoundsExpandFraction = 0.2f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Combat|Thresholds")
	float HeadRegionScale = 0.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Combat|Thresholds")
	float TorsoRegionScale = 1.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Combat|Thresholds")
	float LegRegionScale = 0.7f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Combat|Thresholds")
	float MaxTargetAgeSeconds = 0.75f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Combat|Damage")
	float MaxHealth = 100.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Combat|Damage")
	float RespawnDelaySeconds = 4.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Combat|Feedback")
	float HitWorldDepthCentimeters = 200.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Combat|Feedback")
	bool bSpawnWorldHitMarkers = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Combat|Feedback")
	bool bUseBodycamHudHitMarker = false;

	/** Plays Bodycam HitmarkerEffect on every confirmed body hit. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Combat|Feedback")
	bool bPlayHudHitMarkerBlink = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Combat|Feedback")
	bool bPlayHitSound = false;

	/** Minimum time between hit-confirm sounds to avoid iOS audio voice buildup. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Combat|Feedback", meta = (ClampMin = "0.0"))
	float MinHitSoundIntervalSeconds = 0.1f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Combat|Feedback")
	bool bSpawnBloodEffect = true;

	/** Minimum time between blood VFX replays on the pooled feedback actor. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Combat|Feedback", meta = (ClampMin = "0.0"))
	float MinBloodEffectIntervalSeconds = 0.12f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Combat|Feedback")
	float HitMarkerVisibleSeconds = 0.12f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Combat|Pose2D")
	bool bFlipPose2DY = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Combat|Pose2D")
	bool bUseImageSpacePose2DMapping = true;

	UFUNCTION(BlueprintCallable, Category = "SCAR|Body Combat")
	FSCARBodyCombatHitResult TryApplyShot(
		const UObject* WorldContextObject,
		float BaseDamage,
		float CriticalMultiplier,
		bool bRequirePersonInPreview = true);

	UFUNCTION(BlueprintCallable, Category = "SCAR|Body Combat")
	FSCARBodyCombatHitResult TryApplyShotAtViewport(
		const UObject* WorldContextObject,
		const FVector2D& AimViewport01,
		float BaseDamage,
		float CriticalMultiplier,
		bool bRequirePersonInPreview = true);

	/** Unity ARCombatUiRuntimeBootstrap parity: run Vision assist after the frame's physics hitscan. */
	UFUNCTION(BlueprintCallable, Category = "SCAR|Body Combat")
	void QueueDeferredVisionShot(
		const UObject* WorldContextObject,
		float BaseDamage,
		float CriticalMultiplier,
		bool bRequirePersonInPreview = true);

	UFUNCTION(BlueprintPure, Category = "SCAR|Body Combat")
	static FVector2D GetCombatAimViewport01(const UObject* WorldContextObject);

	UFUNCTION(BlueprintCallable, Category = "SCAR|Body Combat")
	void SpawnHitFeedback(const FSCARBodyCombatHitResult& HitResult);

	bool TryGetTrackedHitViewport01(
		int32 TargetId,
		ESCARVisionBodyJoint AnchorJointA,
		ESCARVisionBodyJoint AnchorJointB,
		float BoneT,
		FVector2D& OutViewport01) const;

	void DrawSkeletonHitMarkerOverlay(UCanvas* Canvas, APlayerController* PlayerController);

	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;
	virtual bool IsTickable() const override;
	virtual bool IsTickableInEditor() const override { return false; }

protected:
	virtual void Deinitialize() override;

private:
	struct FTargetHealthState
	{
		float Health = 0.f;
		double DeadUntilSeconds = 0.0;
	};

	TMap<int32, FTargetHealthState> HealthByTargetId;

	bool BuildAimSamples(
		const USCARBodyDetectionSubsystem* DetectionSubsystem,
		APlayerController* PlayerController,
		TArray<SCARScreenSpaceBodyTargeting::FSCARScreenSpaceAimSample>& OutSamples) const;

	FTargetHealthState& GetOrCreateHealth(int32 TargetId);
	void ResetTargetHealth(int32 TargetId);

	void ShowSkeletonHitMarker(const FSCARBodyCombatHitResult& HitResult);
	void HideSkeletonHitMarker();
	void UpdateSkeletonHitMarkerOverlay();
	UImage* FindHudHitMarkerImage() const;
	bool ApplyHudHitMarkerLayout(UImage* HitMarkerImage, const FVector2D& Viewport01, float SizePx);
	void EnsureFeedbackAssets();
	ASCARBodyHitFeedbackActor* EnsureBloodFeedbackActor();
	void InvalidateHudCache();
	void EnsureCanvasOverlayDrawRegistered();
	void UnregisterCanvasOverlayDraw();
	void OnCanvasOverlayDraw(UCanvas* Canvas, APlayerController* PlayerController);
	void SyncCanvasOverlayDrawRegistration();
	void FlushDeferredVisionShot();
	bool TryGetTrackedHitViewport01Lightweight(FVector2D& OutViewport01) const;

	UPROPERTY()
	TObjectPtr<UTexture2D> HitMarkerTexture;

	UPROPERTY()
	TObjectPtr<UTexture2D> HeadshotMarkerTexture;

	UPROPERTY()
	TObjectPtr<USoundBase> CachedHitSound;

	UPROPERTY()
	TObjectPtr<ASCARBodyHitFeedbackActor> PooledBloodFeedbackActor;

	mutable TWeakObjectPtr<UUserWidget> CachedHudWidget;
	mutable TWeakObjectPtr<UImage> CachedHudHitMarkerImage;
	mutable TWeakObjectPtr<const APawn> CachedHudPawn;
	double LastHitSoundPlaySeconds = -1.0;
	double LastBloodEffectPlaySeconds = -1.0;
	bool bUseCanvasHitMarkerFallback = false;
	bool bForceMarkerLayoutUpdate = false;
	FDelegateHandle CanvasOverlayDrawHandle;
	FVector2D LastAppliedMarkerViewport01 = FVector2D(-1.f, -1.f);
	float LastAppliedMarkerSizePx = -1.f;

	bool bSkeletonHitMarkerVisible = false;
	float SkeletonHitMarkerHideRemaining = 0.f;
	int32 TrackedTargetId = INDEX_NONE;
	ESCARVisionBodyJoint TrackedAnchorJointA = ESCARVisionBodyJoint::Nose;
	ESCARVisionBodyJoint TrackedAnchorJointB = ESCARVisionBodyJoint::Nose;
	float TrackedBoneT = 0.f;
	FVector2D FallbackHitImageUV = FVector2D::ZeroVector;
	FVector2D FallbackHitViewport01 = FVector2D::ZeroVector;
	float MarkerScreenSizePx = 32.f;
	bool bMarkerHeadshot = false;

	struct FPendingDeferredVisionShot
	{
		TWeakObjectPtr<const UObject> WorldContext;
		float BaseDamage = 0.f;
		float CriticalMultiplier = 1.f;
		bool bRequirePersonInPreview = true;
		bool bPending = false;
	};

	FPendingDeferredVisionShot PendingDeferredVisionShot;
};
