#pragma once

#include "CoreMinimal.h"
#include "SCARBodyDetectionTypes.h"
#include "Subsystems/WorldSubsystem.h"
#include "SCARBodyDetectionSubsystem.generated.h"

class USCARVisionBodyPoseProvider;

UCLASS()
class SCAR_API USCARBodyDetectionSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	UPROPERTY(BlueprintAssignable, Category = "SCAR|Body Detection")
	FSCARBodyDetectedDelegate OnBodyDetected;

	UPROPERTY(BlueprintAssignable, Category = "SCAR|Body Detection")
	FSCARBodyLostDelegate OnBodyLost;

	UPROPERTY(BlueprintAssignable, Category = "SCAR|Body Detection")
	FSCARPose2DUpdatedDelegate OnPose2DUpdated;

	UPROPERTY(BlueprintAssignable, Category = "SCAR|Body Detection")
	FSCARVisionTargetsUpdatedDelegate OnVisionTargetsUpdated;

	UPROPERTY(BlueprintAssignable, Category = "SCAR|Body Detection")
	FSCARBodyDetectionUpdatedDelegate OnDetectionUpdated;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Detection")
	bool bEnableVisionMultiBodyDetection = true;

	UFUNCTION(BlueprintPure, Category = "SCAR|Body Detection")
	const FSCARBodyDetectionSnapshot& GetSnapshot() const { return Snapshot; }

	UFUNCTION(BlueprintPure, Category = "SCAR|Body Detection")
	bool IsPersonInCameraPreview() const { return Snapshot.bPersonInCameraPreview; }

	UFUNCTION(BlueprintPure, Category = "SCAR|Body Detection")
	bool Has3DBody() const { return Snapshot.bHas3DBody; }

	UFUNCTION(BlueprintPure, Category = "SCAR|Body Detection")
	bool HasPose2D() const { return Snapshot.bHasPose2D; }

	UFUNCTION(BlueprintPure, Category = "SCAR|Body Detection")
	bool HasVisionTarget() const { return Snapshot.bHasVisionTarget; }

	UFUNCTION(BlueprintPure, Category = "SCAR|Body Detection")
	USCARVisionBodyPoseProvider* GetVisionProvider() const { return VisionProvider; }

	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;
	virtual bool IsTickableInEditor() const override { return false; }

protected:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

private:
	UPROPERTY()
	FSCARBodyDetectionSnapshot Snapshot;

	UPROPERTY()
	TObjectPtr<USCARVisionBodyPoseProvider> VisionProvider;

	bool bHad3DBodyLastFrame = false;
	bool bHadPose2DLastFrame = false;
	bool bHadVisionTargetLastFrame = false;

	void UpdateArkitBodyTracking();
	void UpdateVisionTracking();
	void PublishSnapshot();
};
