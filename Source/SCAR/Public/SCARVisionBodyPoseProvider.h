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

	/** CGImagePropertyOrientation value. Unity default: Right = 6. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Detection")
	int32 VisionImageOrientation = 6;

	UFUNCTION(BlueprintPure, Category = "SCAR|Body Detection")
	bool IsSupported() const;

	UFUNCTION(BlueprintPure, Category = "SCAR|Body Detection")
	const TArray<FSCARScreenSpaceBodyTarget>& GetTargets() const { return Targets; }

	/** Vision image-normalized joint -> UE viewport 01 (top-left origin). */
	UFUNCTION(BlueprintPure, Category = "SCAR|Body Detection")
	static FVector2D NormalizedToViewport01(const FVector2D& VisionNormalized);

	void TickDetection(UWorld* World);

private:
	UPROPERTY()
	TArray<FSCARScreenSpaceBodyTarget> Targets;

	UPROPERTY()
	TArray<FSCARScreenSpaceBodyTarget> PreviousTargets;

	TArray<uint8> RgbaBuffer;
	TArray<float> NativeOutput;
	double NextDetectionTimeSeconds = 0.0;
	int32 NextLocalId = 1;

	bool TryAcquireCameraRgba(UWorld* World, TArray<uint8>& OutRgba, int32& OutWidth, int32& OutHeight) const;
	void BuildTargetsFromNative(int32 BodyCount, double NowSeconds);
	int32 AssociateOrCreateLocalId(const FVector2D& BoundsCenter);
	FVector2D ToViewportPosition(const FVector2D& VisionNormalized) const;
};
