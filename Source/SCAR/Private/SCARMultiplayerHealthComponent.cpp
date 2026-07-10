#include "SCARMultiplayerHealthComponent.h"

#include "GameFramework/Actor.h"
#include "GameFramework/Controller.h"
#include "GameFramework/Pawn.h"
#include "Net/UnrealNetwork.h"
#include "SCARARMultiplayerPlayerState.h"
#include "TimerManager.h"

USCARMultiplayerHealthComponent::USCARMultiplayerHealthComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
	SetIsReplicatedByDefault(true);
}

void USCARMultiplayerHealthComponent::BeginPlay()
{
	Super::BeginPlay();
	ResetHealth();
}

void USCARMultiplayerHealthComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(USCARMultiplayerHealthComponent, Health);
}

float USCARMultiplayerHealthComponent::ApplyDamage(
	const float Damage,
	AActor* DamageCauser,
	const bool bHeadshot)
{
	AActor* Owner = GetOwner();
	if (!Owner || !Owner->HasAuthority() || Damage <= 0.f || !IsAlive())
	{
		return 0.f;
	}

	const float PreviousHealth = Health;
	Health = FMath::Max(0.f, Health - Damage);

	FSCARMultiplayerHitResult HitResult;
	HitResult.bHit = true;
	HitResult.bIsHeadshot = bHeadshot;
	HitResult.AppliedDamage = PreviousHealth - Health;
	HitResult.RemainingHealth = Health;
	HitResult.HitActor = Owner;
	OnDamageTaken.Broadcast(HitResult);

	if (!IsAlive())
	{
		HitResult.bKilledTarget = true;

		if (APawn* VictimPawn = Cast<APawn>(Owner))
		{
			if (ASCARARMultiplayerPlayerState* VictimPS = VictimPawn->GetPlayerState<ASCARARMultiplayerPlayerState>())
			{
				VictimPS->RegisterDeath();
			}
		}

		if (AActor* Causer = DamageCauser)
		{
			if (APawn* KillerPawn = Cast<APawn>(Causer))
			{
				if (ASCARARMultiplayerPlayerState* KillerPS = KillerPawn->GetPlayerState<ASCARARMultiplayerPlayerState>())
				{
					KillerPS->RegisterKill();
				}
			}
			else if (AController* KillerController = Causer->GetInstigatorController())
			{
				if (ASCARARMultiplayerPlayerState* KillerPS = KillerController->GetPlayerState<ASCARARMultiplayerPlayerState>())
				{
					KillerPS->RegisterKill();
				}
			}
		}

		HandleDeath();
	}

	return HitResult.AppliedDamage;
}

void USCARMultiplayerHealthComponent::ResetHealth()
{
	Health = MaxHealth;
}

void USCARMultiplayerHealthComponent::HandleDeath()
{
	AActor* Owner = GetOwner();
	if (!Owner)
	{
		return;
	}

	if (UWorld* World = Owner->GetWorld())
	{
		FTimerHandle RespawnTimer;
		World->GetTimerManager().SetTimer(
			RespawnTimer,
			[this]()
			{
				ResetHealth();
			},
			RespawnDelaySeconds,
			false);
	}
}

void USCARMultiplayerHealthComponent::OnRep_Health()
{
}
