#pragma once

#include "CoreMinimal.h"
#include "ARTypes.h"
#include "SCARBodyDetectionTypes.generated.h"

/** Matches Unity ARScreenSpaceBodyTarget joint order (Vision / MediaPipe). */
UENUM(BlueprintType, meta = (ScriptName = "SCARVisionBodyJointEnum"))
enum class ESCARVisionBodyJoint : uint8
{
	Nose = 0,
	LeftEye,
	RightEye,
	LeftEar,
	RightEar,
	LeftShoulder,
	RightShoulder,
	Neck,
	LeftElbow,
	RightElbow,
	LeftWrist,
	RightWrist,
	LeftHip,
	RightHip,
	Root,
	LeftKnee,
	RightKnee,
	LeftAnkle,
	RightAnkle,
	Count UMETA(Hidden)
};

USTRUCT(BlueprintType)
struct SCAR_API FSCARVisionBodyJoint
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Body Detection")
	FVector2D NormalizedPosition = FVector2D(-1.f, -1.f);

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Body Detection")
	float Confidence = 0.f;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Body Detection")
	bool bIsValid = false;
};

USTRUCT(BlueprintType)
struct SCAR_API FSCARScreenSpaceBodyTarget
{
	GENERATED_BODY()

	static constexpr int32 JointCount = static_cast<int32>(ESCARVisionBodyJoint::Count);

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Body Detection")
	int32 LocalId = INDEX_NONE;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Body Detection")
	float MeanConfidence = 0.f;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Body Detection")
	FVector4 Bounds = FVector4(0.f, 0.f, 1.f, 1.f);

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Body Detection")
	TArray<FSCARVisionBodyJoint> Joints;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Body Detection")
	double LastSeenTimeSeconds = 0.0;

	FSCARScreenSpaceBodyTarget()
	{
		Joints.SetNum(JointCount);
	}
};

USTRUCT(BlueprintType)
struct SCAR_API FSCARBodyDetectionSnapshot
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Body Detection")
	bool bHas3DBody = false;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Body Detection")
	bool bHasPose2D = false;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Body Detection")
	bool bHasVisionTarget = false;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Body Detection")
	bool bPersonInCameraPreview = false;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Body Detection")
	FARPose3D TrackedPose3D;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Body Detection")
	FTransform TrackedPose3DWorldTransform;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Body Detection")
	TArray<FARPose2D> TrackedPoses2D;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Body Detection")
	TArray<FSCARScreenSpaceBodyTarget> VisionTargets;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FSCARBodyDetectedDelegate);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FSCARBodyLostDelegate);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FSCARPose2DUpdatedDelegate, const TArray<FARPose2D>&, Poses2D);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FSCARVisionTargetsUpdatedDelegate, const TArray<FSCARScreenSpaceBodyTarget>&, Targets);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FSCARBodyDetectionUpdatedDelegate, const FSCARBodyDetectionSnapshot&, Snapshot);
