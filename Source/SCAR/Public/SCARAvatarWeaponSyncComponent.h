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

/**
 * Lives on the LOCAL player controller (attached dynamically by
 * ASCARARMultiplayerPlayerController -- no Blueprint edits required).
 *
 * The Bodycam kit spawns weapon items purely locally on the owning device and
 * none of its loadout state replicates, so remote players appear unarmed.
 * This component closes that gap in both directions:
 *
 *  1. OUTGOING: samples the local pawn's held weapon (the kit's SpawnedItem /
 *     SpawnedItemRef item actor's "Item_Mesh"), EquippedWeapon id, and IsAim
 *     flag via reflection, and pushes changes to the local player state via a
 *     Server RPC so everyone receives them.
 *
 *  2. INCOMING: for every remote player pawn, reads the replicated loadout
 *     from that player's state, attaches a weapon mesh to the full-body
 *     avatar's hand socket, and writes EquippedWeapon / IsAim / Equipped onto
 *     the remote pawn's kit variables so its anim blueprint holds and aims
 *     the weapon with the proper stance.
 *
 * Everything is presentation-local except the tiny replicated loadout state
 * on ASCARARMultiplayerPlayerState.
 */
UCLASS(ClassGroup = (SCAR))
class SCAR_API USCARAvatarWeaponSyncComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	USCARAvatarWeaponSyncComponent();

	/** How often the local pawn's loadout is sampled for changes. */
	UPROPERTY(EditAnywhere, Category = "SCAR|AvatarWeapon", meta = (ClampMin = "1.0", ClampMax = "30.0"))
	float SampleRateHz = 5.f;

	/** Body mesh (full-body avatar other players see) component name. */
	UPROPERTY(EditAnywhere, Category = "SCAR|AvatarWeapon")
	FName BodyMeshComponentName = TEXT("CharacterMesh0");

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

		bool operator==(const FLocalLoadoutSample& Other) const
		{
			return WeaponMeshPath == Other.WeaponMeshPath &&
				WeaponId == Other.WeaponId &&
				bAiming == Other.bAiming &&
				AttachSocket == Other.AttachSocket &&
				RelativeLocation.Equals(Other.RelativeLocation, 0.01f) &&
				RelativeRotation.Equals(Other.RelativeRotation, 0.01f);
		}
	};

	// Outgoing: local pawn -> replicated player state.
	void SampleAndSendLocalLoadout(APawn* LocalPawn);
	bool ReadLocalLoadout(APawn* LocalPawn, FLocalLoadoutSample& OutSample) const;
	USkeletalMeshComponent* FindHeldItemMesh(APawn* Pawn) const;

	// Incoming: replicated player state -> remote pawn visuals.
	void UpdateRemoteAvatarWeapons(const APlayerController* LocalPC, const APawn* LocalPawn);
	void ApplyLoadoutToRemotePawn(APawn* Pawn, const ASCARARMultiplayerPlayerState* LoadoutState);
	void ApplyHoldAnimationToBody(APawn* Pawn, USkeletalMeshComponent* BodyMesh, const FString& WeaponMeshPath, bool bArmed);
	USkeletalMeshComponent* EnsureAvatarWeaponComponent(APawn* Pawn, USkeletalMeshComponent* BodyMesh);
	USkeletalMesh* ResolveWeaponMesh(const FString& MeshPath);
	UAnimSequenceBase* ResolveHoldAnimation(const FString& WeaponMeshPath);
	static FName ResolveHandSocket(const USkeletalMeshComponent* BodyMesh);
	static void SetPawnStanceVariables(APawn* Pawn, uint8 WeaponId, bool bAiming, bool bArmed);

	double LastSampleSeconds = 0.0;

	FLocalLoadoutSample LastSentSample;
	bool bHasSentLoadout = false;

	UPROPERTY()
	TMap<FString, TObjectPtr<USkeletalMesh>> WeaponMeshCache;

	UPROPERTY()
	TMap<FString, TObjectPtr<UAnimSequenceBase>> HoldAnimCache;

	UPROPERTY()
	TMap<TObjectPtr<APawn>, TObjectPtr<USkeletalMeshComponent>> AvatarWeaponComponents;

	// Per-pawn anim override bookkeeping so we can restore the kit's
	// locomotion anim blueprint when a player becomes unarmed.
	UPROPERTY()
	TMap<TObjectPtr<APawn>, TObjectPtr<UAnimSequenceBase>> AppliedHoldAnims;

	UPROPERTY()
	TMap<TObjectPtr<APawn>, TSubclassOf<UAnimInstance>> OriginalBodyAnimClasses;
};
