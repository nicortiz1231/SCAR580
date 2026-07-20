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

	/** Asset path of the held weapon's skeletal mesh; empty when unarmed. */
	UPROPERTY(BlueprintReadOnly, Replicated, Category = "SCAR|Multiplayer|Loadout")
	FString HeldWeaponMeshPath;

	UPROPERTY(BlueprintReadOnly, Replicated, Category = "SCAR|Multiplayer|Loadout")
	uint8 EquippedWeaponId = 0;

	UPROPERTY(BlueprintReadOnly, Replicated, Category = "SCAR|Multiplayer|Loadout")
	bool bAvatarAiming = false;

	UPROPERTY(BlueprintReadOnly, Replicated, Category = "SCAR|Multiplayer|Loadout")
	FName HeldWeaponAttachSocket = NAME_None;

	UPROPERTY(BlueprintReadOnly, Replicated, Category = "SCAR|Multiplayer|Loadout")
	FVector HeldWeaponRelativeLocation = FVector::ZeroVector;

	UPROPERTY(BlueprintReadOnly, Replicated, Category = "SCAR|Multiplayer|Loadout")
	FRotator HeldWeaponRelativeRotation = FRotator::ZeroRotator;

	/** One-shot avatar action (1=Fire, 2=Reload, 3=ReloadEmpty). */
	UPROPERTY(BlueprintReadOnly, Replicated, Category = "SCAR|Multiplayer|Loadout")
	uint8 AvatarAnimAction = 0;

	UPROPERTY(BlueprintReadOnly, Replicated, Category = "SCAR|Multiplayer|Loadout")
	uint8 AvatarAnimActionSerial = 0;

	UFUNCTION(Server, Reliable)
	void Server_UpdateAvatarLoadout(
		const FString& WeaponMeshPath,
		uint8 WeaponId,
		bool bAiming,
		FName AttachSocket,
		FVector RelativeLocation,
		FRotator RelativeRotation);

	/** Owning client -> server: fire / reload one-shot for remote avatars. */
	UFUNCTION(Server, Reliable)
	void Server_NotifyAvatarAnimAction(uint8 Action);

	/** Server -> all clients: play fire/reload on this player's visible mannequin. */
	UFUNCTION(NetMulticast, Reliable)
	void Multicast_PlayAvatarAnimAction(uint8 Action, uint8 Serial);

protected:
	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	UFUNCTION()
	void OnRep_Kills();

	UFUNCTION()
	void OnRep_Deaths();

private:
	void PlayAvatarActionOnPawn(uint8 Action) const;

	double LastServerAvatarActionSeconds = -1000.0;
	uint8 LastServerAvatarAction = 0;
};
