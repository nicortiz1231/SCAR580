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
