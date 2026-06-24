#pragma once

#include "CoreMinimal.h"
#include "SCARBodyDetectionTypes.h"
#include "SCARBodyCombatTypes.generated.h"

UENUM(BlueprintType)
enum class ESCARBodyHitRegion : uint8
{
	None,
	Head,
	Torso,
	Legs
};

USTRUCT(BlueprintType)
struct SCAR_API FSCARBodyCombatHitResult
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Body Combat")
	bool bHit = false;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Body Combat")
	bool bIsHeadshot = false;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Body Combat")
	bool bKilledTarget = false;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Body Combat")
	int32 TargetId = INDEX_NONE;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Body Combat")
	ESCARBodyHitRegion HitRegion = ESCARBodyHitRegion::None;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Body Combat")
	ESCARVisionBodyJoint HitJoint = ESCARVisionBodyJoint::Nose;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Body Combat")
	FVector HitWorldLocation = FVector::ZeroVector;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Body Combat")
	FVector2D HitViewport01 = FVector2D::ZeroVector;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Body Combat")
	FVector2D HitMarkerJointOffset = FVector2D::ZeroVector;

	/** Camera-image normalized hit point used to keep markers pinned while the device moves. */
	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Body Combat")
	FVector2D HitImageUV = FVector2D::ZeroVector;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Body Combat")
	ESCARVisionBodyJoint HitAnchorJointA = ESCARVisionBodyJoint::Root;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Body Combat")
	ESCARVisionBodyJoint HitAnchorJointB = ESCARVisionBodyJoint::Root;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Body Combat")
	float HitAnchorBoneT = 0.f;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Body Combat")
	float AppliedDamage = 0.f;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Body Combat")
	float RemainingHealth = 0.f;

	UPROPERTY(BlueprintReadOnly, Category = "SCAR|Body Combat")
	float HitMarkerScreenSizePx = 32.f;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FSCARBodyCombatHitDelegate, const FSCARBodyCombatHitResult&, HitResult);
