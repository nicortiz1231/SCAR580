#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SCARMultiplayerPresentationComponent.generated.h"

class USkeletalMeshComponent;

/** Remote opponent: mirrored mannequin driven by hidden FP arms + pistol at hipfire grip. */
UCLASS(ClassGroup = (SCAR), meta = (BlueprintSpawnableComponent))
class SCAR_API USCARMultiplayerPresentationComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	USCARMultiplayerPresentationComponent();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Multiplayer|Presentation")
	TSoftObjectPtr<USkeletalMesh> OpponentMannequinMesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Multiplayer|Presentation")
	TSoftObjectPtr<USkeletalMesh> OpponentFpArmsMesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Multiplayer|Presentation")
	TSubclassOf<UAnimInstance> OpponentMirrorAnimClass;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Multiplayer|Presentation")
	TSubclassOf<UAnimInstance> OpponentPoseDriverAnimClass;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Multiplayer|Presentation")
	TSoftObjectPtr<USkeletalMesh> OpponentFallbackPistolMesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Multiplayer|Presentation")
	FName OpponentWeaponAttachSocketName = TEXT("ik_hand_gun");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Multiplayer|Presentation")
	FName ThirdPersonMeshComponentName = TEXT("CharacterMesh0");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Multiplayer|Presentation")
	FName FirstPersonMeshComponentName = TEXT("CharacterMesh");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Multiplayer|Presentation")
	FVector PoseDriverRelativeLocation = FVector(15.f, 0.f, 65.f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Multiplayer|Presentation")
	FRotator PoseDriverRelativeRotation = FRotator(0.f, 0.f, 0.f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Multiplayer|Presentation")
	FName OpponentWeaponComponentName = TEXT("SCAR_OpponentWeapon");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Multiplayer|Presentation")
	FName OpponentPoseDriverComponentName = TEXT("SCAR_OpponentPoseDriver");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Multiplayer|Presentation")
	bool bPlaceOpponentInView = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Multiplayer|Presentation", meta = (ClampMin = "50.0"))
	float OpponentViewDistanceCm = 260.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Multiplayer|Presentation")
	bool bShowOpponentDebug = false;

	bool IsUsingViewPlacementForLocalViewer() const;

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
	UFUNCTION()
	void OnPawnControllerChanged(APawn* Pawn, AController* OldController, AController* NewController);

	bool ShouldShowOpponentForLocalViewer(const APawn* Pawn) const;
	void ConfigureNetworkVisibility(AActor* OwnerActor) const;
	void RefreshPresentation();
	void UpdateOpponentViewPlacement();
	void ShowOpponentDebug(const APawn* Pawn) const;
	USkeletalMeshComponent* FindMeshByExactName(APawn* Pawn, FName ComponentName) const;
	USkeletalMesh* ResolveOpponentMannequinMesh();
	USkeletalMesh* ResolveOpponentFpArmsMesh();
	USkeletalMesh* ResolveOpponentFallbackPistolMesh();
	TSubclassOf<UAnimInstance> ResolveOpponentMirrorAnimClass() const;
	TSubclassOf<UAnimInstance> ResolveOpponentPoseDriverAnimClass() const;
	void ReparentPoseDriverToPawnRoot(APawn* Pawn, USkeletalMeshComponent* PoseDriverMesh) const;
	USkeletalMeshComponent* EnsurePoseDriverMesh(APawn* Pawn);
	void ConfigureFpPoseDriver(APawn* Pawn, USkeletalMeshComponent* PoseDriverMesh);
	void ConfigureMirroredMannequin(USkeletalMeshComponent* MannequinMesh);
	void ReinitializeMirrorAnimIfNeeded(USkeletalMeshComponent* MannequinMesh);
	void EnsurePawnEquippedGunSetForOpponentView(APawn* Pawn) const;
	void HideCameraAndLightComponents(APawn* Pawn) const;
	void EnsureOpponentWeaponOnMannequin(APawn* Pawn, USkeletalMeshComponent* MannequinMesh);
	USkeletalMeshComponent* FindExistingPistolItemMesh(APawn* Pawn) const;
	FName ResolveWeaponAttachSocket(const USkeletalMeshComponent* PoseDriverMesh) const;
	void SetComponentWorldVisible(UPrimitiveComponent* Component) const;
	void SetComponentHidden(UPrimitiveComponent* Component, bool bHidden) const;
	FVector ComputeOpponentViewLocation(const APawn* Pawn, const FVector& ViewLocation, const FRotator& ViewRotation) const;

	UPROPERTY()
	TObjectPtr<USkeletalMeshComponent> OpponentMannequinMeshComponent;

	UPROPERTY()
	TObjectPtr<USkeletalMeshComponent> OpponentPoseDriverMeshComponent;

	UPROPERTY()
	TObjectPtr<USkeletalMeshComponent> OpponentWeaponMeshComponent;

	UPROPERTY()
	TObjectPtr<USkeletalMeshComponent> ReusedPistolItemMesh;

	UPROPERTY()
	TObjectPtr<USkeletalMesh> CachedMannequinMesh;

	UPROPERTY()
	TObjectPtr<USkeletalMesh> CachedFpArmsMesh;

	UPROPERTY()
	TObjectPtr<USkeletalMesh> CachedFallbackPistolMesh;

	float OpponentRefreshAccumulator = 0.f;

	bool bCachedIsOpponentView = false;

	bool bMirrorAnimInitialized = false;
};
