#include "SCARARMultiplayerPlayerState.h"

#include "Net/UnrealNetwork.h"

ASCARARMultiplayerPlayerState::ASCARARMultiplayerPlayerState()
{
	bReplicates = true;
	SetNetUpdateFrequency(10.f);
}

void ASCARARMultiplayerPlayerState::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(ASCARARMultiplayerPlayerState, Kills);
	DOREPLIFETIME(ASCARARMultiplayerPlayerState, Deaths);
	DOREPLIFETIME(ASCARARMultiplayerPlayerState, HeldWeaponMeshPath);
	DOREPLIFETIME(ASCARARMultiplayerPlayerState, EquippedWeaponId);
	DOREPLIFETIME(ASCARARMultiplayerPlayerState, bAvatarAiming);
	DOREPLIFETIME(ASCARARMultiplayerPlayerState, HeldWeaponAttachSocket);
	DOREPLIFETIME(ASCARARMultiplayerPlayerState, HeldWeaponRelativeLocation);
	DOREPLIFETIME(ASCARARMultiplayerPlayerState, HeldWeaponRelativeRotation);
}

void ASCARARMultiplayerPlayerState::Server_UpdateAvatarLoadout_Implementation(
	const FString& WeaponMeshPath,
	const uint8 WeaponId,
	const bool bAiming,
	const FName AttachSocket,
	const FVector RelativeLocation,
	const FRotator RelativeRotation)
{
	HeldWeaponMeshPath = WeaponMeshPath;
	EquippedWeaponId = WeaponId;
	bAvatarAiming = bAiming;
	HeldWeaponAttachSocket = AttachSocket;
	HeldWeaponRelativeLocation = RelativeLocation;
	HeldWeaponRelativeRotation = RelativeRotation;
}

void ASCARARMultiplayerPlayerState::RegisterKill()
{
	if (HasAuthority())
	{
		++Kills;
	}
}

void ASCARARMultiplayerPlayerState::RegisterDeath()
{
	if (HasAuthority())
	{
		++Deaths;
	}
}

void ASCARARMultiplayerPlayerState::OnRep_Kills()
{
}

void ASCARARMultiplayerPlayerState::OnRep_Deaths()
{
}
