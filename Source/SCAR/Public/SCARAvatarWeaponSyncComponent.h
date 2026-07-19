#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Templates/SubclassOf.h"
#include "SCARAvatarWeaponSyncComponent.generated.h"

class APawn;
class APlayerController;
class ASCARARMultiplayerPlayerState;
class UAnimInstance;
class UAnimSequenceBase;
class USkeletalMesh;
class USkeletalMeshComponent;

/** Avatar one-shot actions mirrored to remote mannequins. */
UENUM(BlueprintType)
enum class ESCARAvatarAnimAction : uint8
{
	None = 0,
	Fire = 1,
	Reload = 2,
	ReloadEmpty = 3,
};

/**
 * Lives on the LOCAL player controller.
 *
 * Remote CharacterMesh0 keeps ABP_Manny so look / turn / loco stay alive.
 * Stance vars + EquippedAnimset select the kit upper-body weapon hold.
 * Aim pitch is driven by PoseSync -> SetRemoteViewPitch (not whole-mesh tip).
 * Fire / reload play as UpperBody slot montages. Local FP arms are untouched.
 */
UCLASS(ClassGroup = (SCAR))
class SCAR_API USCARAvatarWeaponSyncComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	USCARAvatarWeaponSyncComponent();

	UPROPERTY(EditAnywhere, Category = "SCAR|AvatarWeapon", meta = (ClampMin = "1.0", ClampMax = "30.0"))
	float SampleRateHz = 10.f;

	UPROPERTY(EditAnywhere, Category = "SCAR|AvatarWeapon")
	FName BodyMeshComponentName = TEXT("CharacterMesh0");

	UPROPERTY(EditAnywhere, Category = "SCAR|AvatarWeapon")
	FName UpperBodySlotName = TEXT("UpperBody");

protected:
	virtual void TickComponent(
		float DeltaTime,
		ELevelTick TickType,
		FActorComponentTickFunction* ThisTickFunction) override;

private:
	struct FLocalLoadoutSample
	{
		FString WeaponMeshPath;
		uint8 WeaponId = 0;
		bool bAiming = false;
		FName AttachSocket = NAME_None;
		FVector RelativeLocation = FVector::ZeroVector;
		FRotator RelativeRotation = FRotator::ZeroRotator;
		ESCARAvatarAnimAction Action = ESCARAvatarAnimAction::None;

		bool operator==(const FLocalLoadoutSample& Other) const
		{
			return WeaponMeshPath == Other.WeaponMeshPath &&
				WeaponId == Other.WeaponId &&
				bAiming == Other.bAiming &&
				AttachSocket == Other.AttachSocket &&
				RelativeLocation.Equals(Other.RelativeLocation, 0.01f) &&
				RelativeRotation.Equals(Other.RelativeRotation, 0.01f) &&
				Action == Other.Action;
		}
	};

	void SampleAndSendLocalLoadout(APawn* LocalPawn);
	bool ReadLocalLoadout(APawn* LocalPawn, FLocalLoadoutSample& OutSample) const;
	ESCARAvatarAnimAction DetectLocalAnimAction(APawn* LocalPawn);
	USkeletalMeshComponent* FindHeldItemMesh(APawn* Pawn) const;

	void UpdateRemoteAvatarWeapons(const APlayerController* LocalPC, const APawn* LocalPawn);
	void ApplyLoadoutToRemotePawn(APawn* Pawn, const ASCARARMultiplayerPlayerState* LoadoutState);
	void EnsureMannyAnimBP(APawn* Pawn, USkeletalMeshComponent* BodyMesh);
	void ApplyWeaponStance(APawn* Pawn, USkeletalMeshComponent* BodyMesh, const FString& WeaponMeshPath, bool bArmed, bool bAiming);
	void ApplyAvatarAction(APawn* Pawn, USkeletalMeshComponent* BodyMesh, ESCARAvatarAnimAction Action, uint8 Serial, const FString& WeaponMeshPath);
	void DestroyLeftoverAdsDrivers(APawn* Pawn);
	USkeletalMeshComponent* EnsureAvatarWeaponComponent(APawn* Pawn, USkeletalMeshComponent* BodyMesh);
	USkeletalMesh* ResolveWeaponMesh(const FString& MeshPath);
	UAnimSequenceBase* ResolveHoldAnimation(const FString& WeaponMeshPath, bool bAiming);
	UAnimSequenceBase* ResolveActionAnimation(const FString& WeaponMeshPath, ESCARAvatarAnimAction Action);
	static uint8 ResolveAnimsetForWeapon(const FString& WeaponMeshPath);
	static FName ResolveHandSocket(const USkeletalMeshComponent* BodyMesh);
	static void SetPawnStanceVariables(APawn* Pawn, uint8 WeaponId, bool bAiming, bool bArmed);
	static void HideDuplicatePresentationWeapons(APawn* Pawn);

	double LastSampleSeconds = 0.0;

	FLocalLoadoutSample LastSentSample;
	bool bHasSentLoadout = false;
	ESCARAvatarAnimAction LastDetectedAction = ESCARAvatarAnimAction::None;
	float LastFireAlpha = 0.f;

	UPROPERTY()
	TMap<FString, TObjectPtr<USkeletalMesh>> WeaponMeshCache;

	UPROPERTY()
	TMap<FString, TObjectPtr<UAnimSequenceBase>> HoldAnimCache;

	UPROPERTY()
	TMap<TObjectPtr<APawn>, TObjectPtr<USkeletalMeshComponent>> AvatarWeaponComponents;

	UPROPERTY()
	TMap<TObjectPtr<APawn>, uint8> LastPlayedActionSerial;

	UPROPERTY()
	TMap<TObjectPtr<APawn>, TSubclassOf<UAnimInstance>> OriginalBodyAnimClasses;
};
