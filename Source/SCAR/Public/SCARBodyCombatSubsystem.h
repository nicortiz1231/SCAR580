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
	float MaxBoneDistanceNormalized = 0.048f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Combat|Thresholds")
	float BoundsPaddingNormalized = 0.012f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Combat|Thresholds")
	float HeadRegionScale = 0.18f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Combat|Thresholds")
	float TorsoRegionScale = 0.66f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Combat|Thresholds")
	float LegRegionScale = 0.4f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Combat|Thresholds")
	float MaxTargetAgeSeconds = 0.35f;

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

	/** Plays Bodycam HitmarkerEffect once per blink; skipped while marker is already visible. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Combat|Feedback")
	bool bPlayHudHitMarkerBlink = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Combat|Feedback")
	bool bPlayHitSound = true;

	/** Minimum time between hit-confirm sounds to avoid iOS audio voice buildup. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Combat|Feedback", meta = (ClampMin = "0.0"))
	float MinHitSoundIntervalSeconds = 0.1f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Combat|Feedback")
	bool bSpawnBloodEffect = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Combat|Feedback")
	float HitMarkerVisibleSeconds = 0.08f;

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
	double LastHudBlinkPlaySeconds = -1.0;
	bool bUseCanvasHitMarkerFallback = false;
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
};
