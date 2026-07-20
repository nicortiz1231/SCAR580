#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SCARLocalFirstPersonArmsComponent.generated.h"

class UCameraComponent;
class USkeletalMeshComponent;
class USpringArmComponent;
class APawn;

/**
 * Local AR FPS view: camera-locked arms visible only to the owning player,
 * while CharacterMesh0 remains the full-body avatar other clients see.
 *
 * AR passthrough video tilts with the physical phone, but the rendered FP
 * arms overlay must show zero roll on screen -- the world appears to lean
 * behind arms that stay visually fixed (classic Bodycam AR feel). Pitch/yaw
 * still track look direction; roll is stripped from ControlRotation and the
 * spring arm. CharacterMesh is parented to FirstPersonCamera and its
 * component transform is reset each frame after procedural ADS so ADS does
 * not cant the whole mesh off-axis.
 *
 * CharacterMesh0 is the separate full-body mannequin other players see. It is
 * driven by sanitized AR body pose (yaw/pitch, roll stripped) so awkward phone
 * holds -- even upside down -- never flip the local FP view or the multiplayer
 * avatar.
 */
UCLASS(ClassGroup = (SCAR), meta = (BlueprintSpawnableComponent))
class SCAR_API USCARLocalFirstPersonArmsComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	USCARLocalFirstPersonArmsComponent();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|FirstPerson")
	FName FirstPersonCameraComponentName = TEXT("FirstPersonCamera");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|FirstPerson")
	FName SpringArmComponentName = TEXT("SpringArm");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|FirstPerson")
	FName FirstPersonMeshComponentName = TEXT("CharacterMesh");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|FirstPerson")
	FName ThirdPersonMeshComponentName = TEXT("CharacterMesh0");

protected:
	virtual void BeginPlay() override;
	virtual void TickComponent(
		float DeltaTime,
		ELevelTick TickType,
		FActorComponentTickFunction* ThisTickFunction) override;

private:
	void TrySetup(APawn* Pawn);
	void ConfigureLocalView(APawn* Pawn);
	void EnsureFirstPersonMeshOnCamera(APawn* Pawn);
	void LockFirstPersonMeshToCamera();
	void ConfigureMultiplayerBodyMesh(APawn* Pawn);
	void ConfigureEditorDesktopBodyMesh(APawn* Pawn);
	void ConfigureSpringArmForAR();
	void DisableCameraLookSwayForAR(APawn* Pawn);
	bool IsARRunning() const;
	UCameraComponent* FindFirstPersonCamera(const APawn* Pawn) const;
	USpringArmComponent* FindSpringArm(const APawn* Pawn) const;
	USkeletalMeshComponent* FindMeshByExactName(const APawn* Pawn, FName Name) const;

	UPROPERTY()
	TObjectPtr<UCameraComponent> CachedFirstPersonCamera;

	UPROPERTY()
	TObjectPtr<USpringArmComponent> CachedSpringArm;

	UPROPERTY()
	TObjectPtr<USkeletalMeshComponent> CachedFirstPersonMesh;

	UPROPERTY()
	TObjectPtr<USkeletalMeshComponent> CachedThirdPersonMesh;

	FVector CameraAttachRelativeLocation = FVector::ZeroVector;
	FRotator CameraAttachRelativeRotation = FRotator::ZeroRotator;
	FVector CameraAttachRelativeScale = FVector::OneVector;

	bool bLocalViewConfigured = false;
	bool bSpringArmConfiguredForAR = false;
	bool bCameraLookSwayDisabled = false;
	bool bEditorDesktopBodyConfigured = false;
};
