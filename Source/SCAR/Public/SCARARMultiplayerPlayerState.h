#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerState.h"
#include "SCARARMultiplayerPlayerState.generated.h"

UCLASS()
class SCAR_API ASCARARMultiplayerPlayerState : public APlayerState
{
	GENERATED_BODY()

public:
	ASCARARMultiplayerPlayerState();

	UPROPERTY(BlueprintReadOnly, ReplicatedUsing = OnRep_Kills, Category = "SCAR|Multiplayer")
	int32 Kills = 0;

	UPROPERTY(BlueprintReadOnly, ReplicatedUsing = OnRep_Deaths, Category = "SCAR|Multiplayer")
	int32 Deaths = 0;

	UFUNCTION(BlueprintCallable, Category = "SCAR|Multiplayer")
	void RegisterKill();

	UFUNCTION(BlueprintCallable, Category = "SCAR|Multiplayer")
	void RegisterDeath();

	// --- Avatar loadout, so remote machines can show this player's weapon ---
	// The Bodycam kit spawns weapon items purely locally on the owning device,
	// so the held weapon's identity is replicated here (owning client samples
	// its pawn and pushes changes via Server RPC). Viewing machines rebuild
	// the visual from this state; see USCARAvatarWeaponSyncComponent.

	/** Asset path of the held weapon's skeletal mesh; empty when unarmed. */
	UPROPERTY(BlueprintReadOnly, Replicated, Category = "SCAR|Multiplayer|Loadout")
	FString HeldWeaponMeshPath;

	/** Kit's EquippedWeapon byte (weapon slot/animset id) for stance matching. */
	UPROPERTY(BlueprintReadOnly, Replicated, Category = "SCAR|Multiplayer|Loadout")
	uint8 EquippedWeaponId = 0;

	/** Whether the player is aiming down sights. */
	UPROPERTY(BlueprintReadOnly, Replicated, Category = "SCAR|Multiplayer|Loadout")
	bool bAvatarAiming = false;

	/** Skeleton socket the kit attached the held weapon to (e.g. ik_hand_gun). */
	UPROPERTY(BlueprintReadOnly, Replicated, Category = "SCAR|Multiplayer|Loadout")
	FName HeldWeaponAttachSocket = NAME_None;

	/** Kit's per-weapon grip offset relative to the attach socket. */
	UPROPERTY(BlueprintReadOnly, Replicated, Category = "SCAR|Multiplayer|Loadout")
	FVector HeldWeaponRelativeLocation = FVector::ZeroVector;

	UPROPERTY(BlueprintReadOnly, Replicated, Category = "SCAR|Multiplayer|Loadout")
	FRotator HeldWeaponRelativeRotation = FRotator::ZeroRotator;

	UFUNCTION(Server, Reliable)
	void Server_UpdateAvatarLoadout(
		const FString& WeaponMeshPath,
		uint8 WeaponId,
		bool bAiming,
		FName AttachSocket,
		FVector RelativeLocation,
		FRotator RelativeRotation);

protected:
	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	UFUNCTION()
	void OnRep_Kills();

	UFUNCTION()
	void OnRep_Deaths();
};
