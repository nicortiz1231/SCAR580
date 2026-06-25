#pragma once

#include "CoreMinimal.h"
#include "SCARBodyDetectionTypes.h"
#include "SCARVisionBodyPoseProvider.generated.h"

/**
 * Apple Vision multi-body 2D pose on AR camera CPU frames.
 * Mirrors Unity ARVisionMultiBodyPoseProvider / ARScreenSpaceMultiBodyPoseProviderBase.
 */
UCLASS(BlueprintType)
class SCAR_API USCARVisionBodyPoseProvider : public UObject
{
	GENERATED_BODY()

public:
	static constexpr int32 MaxBodies = 8;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Detection")
	float DetectionIntervalSeconds = 0.12f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Detection")
	int32 MaxImageDimension = 320;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Detection")
	float MinJointConfidence = 0.25f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Detection")
	float MaxAssociationDistance = 0.18f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Detection")
	bool bMirrorViewportX = false;

	/** CGImagePropertyOrientation value. Unity default: Right = 6. Auto-updated when bAutoDetectOrientation is true. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Detection")
	int32 VisionImageOrientation = 6;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Detection")
	bool bAutoDetectOrientation = true;

	UFUNCTION(BlueprintPure, Category = "SCAR|Body Detection")
	bool IsSupported() const;

	UFUNCTION(BlueprintPure, Category = "SCAR|Body Detection")
	const TArray<FSCARScreenSpaceBodyTarget>& GetTargets() const { return Targets; }

	UFUNCTION(BlueprintPure, Category = "SCAR|Body Detection|Debug")
	int32 GetDebugLastBodyCount() const { return DebugLastBodyCount; }

	UFUNCTION(BlueprintPure, Category = "SCAR|Body Detection|Debug")
	int32 GetDebugLastOrientation() const { return DebugLastOrientation; }

	UFUNCTION(BlueprintPure, Category = "SCAR|Body Detection|Debug")
	FString GetDebugLastCameraSource() const { return DebugLastCameraSource; }

	UFUNCTION(BlueprintPure, Category = "SCAR|Body Detection|Debug")
	bool GetDebugHadCameraBuffer() const { return bDebugHadCameraBuffer; }

	/** Vision viewport bottom-left 01 -> UE viewport top-left 01 (Unity ARScreenSpaceBodyTarget parity). */
	UFUNCTION(BlueprintPure, Category = "SCAR|Body Detection")
	static FVector2D NormalizedToViewport01(const FVector2D& VisionNormalized);

	void TickDetection(UWorld* World);

private:
	UPROPERTY()
	TArray<FSCARScreenSpaceBodyTarget> Targets;

	UPROPERTY()
	TArray<FSCARScreenSpaceBodyTarget> PreviousTargets;

	TArray<float> NativeOutput;
	double NextDetectionTimeSeconds = 0.0;
	int32 NextLocalId = 1;
	int32 CachedAutoOrientation = 6;

	int32 DebugLastBodyCount = 0;
	int32 DebugLastOrientation = 6;
	FString DebugLastCameraSource = TEXT("none");
	bool bDebugHadCameraBuffer = false;

	bool TryRunDetectionFromCamera(UWorld* World, int32& OutBodyCount);
	int32 RunVisionOnPixelBuffer(void* PixelBuffer);
	void BuildTargetsFromNative(int32 BodyCount, double NowSeconds);
	void PruneStaleTargets(double NowSeconds, float MaxAgeSeconds);
	int32 AssociateOrCreateLocalId(const FVector2D& BoundsCenter, TArray<bool>& PreviousUsed);
	FVector2D ToViewportPosition(const FVector2D& VisionNormalized) const;
};
