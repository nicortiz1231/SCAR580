#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SCARARPoseSyncComponent.generated.h"

/** Samples ARKit camera pose on the owning device and replicates it for opponent placement. */
UCLASS(ClassGroup = (SCAR), meta = (BlueprintSpawnableComponent))
class SCAR_API USCARARPoseSyncComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	USCARARPoseSyncComponent();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|AR Pose")
	bool bDriveOwnerFromARPose = true;

	/** World-space offset applied after the AR camera pose (body vs. camera). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|AR Pose")
	FVector BodyOffsetFromCamera = FVector(0.f, 0.f, -160.f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|AR Pose", meta = (ClampMin = "1.0", ClampMax = "60.0"))
	float PoseSendRateHz = 20.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|AR Pose", meta = (ClampMin = "1.0", ClampMax = "30.0"))
	float ProxyInterpolationSpeed = 12.f;

	UPROPERTY(BlueprintReadOnly, ReplicatedUsing = OnRep_ReplicatedARPose, Category = "SCAR|AR Pose")
	FTransform ReplicatedARPose = FTransform::Identity;

	UFUNCTION(BlueprintPure, Category = "SCAR|AR Pose")
	bool HasValidARPose() const { return bHasValidARPose; }

	UFUNCTION(BlueprintPure, Category = "SCAR|AR Pose")
	FTransform GetCurrentARPose() const;

	/** Session origin for the local viewer pawn, used to place remote players nearby. */
	static FTransform GetLocalViewerSessionOrigin(const UWorld* World);

protected:
	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	UFUNCTION()
	void OnRep_ReplicatedARPose();

	UFUNCTION(Server, Unreliable)
	void Server_UpdateARPose(FVector_NetQuantize Location, FRotator Rotation);

private:
	bool SampleARPose(FTransform& OutPose) const;
	void CaptureSessionOriginIfNeeded(const FTransform& CurrentPose);
	FTransform ComputeWorldPoseFromSessionRelative(const FTransform& RelativePose) const;
	void ApplyPoseToOwner(const FTransform& Pose, bool bTeleport);
	void UpdateProxyInterpolation(float DeltaTime);
	void UpdateRemoteProxyPose(float DeltaTime);

	bool bHasValidARPose = false;
	bool bHasLocalSessionOrigin = false;
	bool bHasSnappedRemotePose = false;
	double LastPoseSendSeconds = 0.0;
	FTransform LocalSessionOrigin = FTransform::Identity;
	FTransform ProxyTargetPose = FTransform::Identity;
};
